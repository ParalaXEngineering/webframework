from flask import Blueprint, render_template, request

from ..modules import utilities
from ..modules import displayer
from ..modules import site_conf
from ..modules import User_defined_module
from ..modules.auth.auth_manager import auth_manager
from ..modules.settings import SettingsManager
from ..modules.utilities import get_config_or_error

from redminelib import Redmine

import redminelib
import os
import zipfile
import glob
import re
import base64
import hashlib
from datetime import datetime
from bs4 import BeautifulSoup
import textile

bp = Blueprint("bug", __name__, url_prefix="/bug")


def get_settings_manager():
    """Get or create settings manager instance."""
    global _settings_manager
    if '_settings_manager' not in globals():
        config_path = os.path.join(os.getcwd(), "config.json")
        globals()['_settings_manager'] = SettingsManager(config_path)
        globals()['_settings_manager'].load()
    return globals()['_settings_manager']


@bp.route("/edit/<int:issue_id>", methods=["GET", "POST"])
def edit_issue(issue_id):
    """Edit an existing Redmine issue."""
    settings_mgr = get_settings_manager()
    disp = displayer.Displayer()
    User_defined_module.User_defined_module.m_default_name = f"Edit Issue ID {issue_id}"
    disp.add_module(User_defined_module.User_defined_module)

    if site_conf.site_conf_obj and not site_conf.site_conf_obj.m_globals["on_target"]:
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        # Get Redmine configuration
        configs, error = get_config_or_error(settings_mgr, 
                                             "redmine.address.value",
                                             "redmine.user.value",
                                             "redmine.password.value")
        if error:
            return error

        try:
            redmine = Redmine(
                configs["redmine.address.value"], 
                username=configs["redmine.user.value"], 
                password=configs["redmine.password.value"], 
                requests={"verify": False}
            )
            
            # Get the issue
            issue = redmine.issue.get(issue_id)
            
        except redminelib.exceptions.ResourceNotFoundError:
            return render_template("error.j2", message=f"Issue #{issue_id} was not found in Redmine.")
        except Exception as e:
            return render_template("error.j2", message=f"Error connecting to Redmine: {e}")

        if request.method == "POST":
            data_in = utilities.util_post_to_json(request.form.to_dict())
            # Get the form data - the key should be "Edit Issue ID: {issue_id}"
            form_key = f"Edit Issue ID: {issue_id}"
            if form_key not in data_in:
                # Fallback: try to find any key with "Edit Issue"
                form_key = next((k for k in data_in.keys() if "Edit Issue" in k), None)
                if not form_key:
                    return render_template("error.j2", message="Invalid form submission")
            
            form_data = data_in[form_key]
            
            if len(form_data.get("description", "")) < 5:
                return render_template("error.j2", message="Please provide a meaningful description")
            if len(form_data.get("subject", "")) < 5:
                return render_template("error.j2", message="Please provide a meaningful subject")

            # Convert HTML description to Redmine textile format
            description_html = form_data.get("description", "")
            description_textile, embedded_images = html_to_redmine_textile(description_html)

            try:
                current_user = "GUEST"
                if auth_manager:
                    current_user = auth_manager.get_current_user() or "GUEST"
                
                # Prepare update data
                update_data = {
                    'subject': form_data["subject"],
                    'description': description_textile + '\r\n\r\n' + f"_Last edited by User {current_user}_"
                }
                
                # Handle embedded images - check if they already exist by comparing hashes
                uploads_list = []
                
                # Get existing image attachments and their hashes
                existing_images = {}
                if hasattr(issue, 'attachments'):
                    for attachment in issue.attachments:
                        if attachment.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp')):
                            try:
                                img_response = attachment.download()
                                if hasattr(img_response, 'content'):
                                    img_bytes = img_response.content
                                elif hasattr(img_response, 'read'):
                                    img_bytes = img_response.read()
                                else:
                                    img_bytes = img_response
                                img_hash = hashlib.md5(img_bytes).hexdigest()
                                existing_images[img_hash] = attachment.filename
                            except Exception:
                                pass
                
                # Process embedded images - only upload if new or changed
                for img_data in embedded_images:
                    img_hash = hashlib.md5(img_data['data']).hexdigest()
                    
                    # Check if this exact image already exists
                    if img_hash in existing_images:
                        # Image already exists - update the textile reference to use existing filename
                        old_filename = img_data['filename']
                        existing_filename = existing_images[img_hash]
                        # Update the description to reference the existing image
                        update_data['description'] = update_data['description'].replace(
                            f"!{old_filename}!",
                            f"!{existing_filename}!"
                        )
                    else:
                        # New or changed image - upload it
                        # Find a unique filename if needed
                        base_name = img_data['filename'].rsplit('.', 1)[0]
                        extension = img_data['filename'].rsplit('.', 1)[1]
                        new_filename = img_data['filename']
                        counter = 1
                        
                        # Check if filename already exists with different content
                        while any(att.filename == new_filename for att in issue.attachments):
                            new_filename = f"{base_name}_v{counter}.{extension}"
                            counter += 1
                        
                        # Update the textile reference if filename changed
                        if new_filename != img_data['filename']:
                            update_data['description'] = update_data['description'].replace(
                                f"!{img_data['filename']}!",
                                f"!{new_filename}!"
                            )
                        
                        temp_img_path = os.path.join(os.getcwd(), new_filename)
                        with open(temp_img_path, 'wb') as f:
                            f.write(img_data['data'])
                        uploads_list.append({'path': temp_img_path, 'description': f"Embedded image: {new_filename}"})
                
                if uploads_list:
                    update_data['uploads'] = uploads_list
                
                # Update the issue
                redmine.issue.update(issue_id, **update_data)
                
                # Clean up temporary image files
                for upload_info in uploads_list:
                    temp_img_path = upload_info['path']
                    if os.path.exists(temp_img_path):
                        try:
                            os.remove(temp_img_path)
                        except Exception:
                            pass
                
                # Redirect back to bug tracker
                from flask import redirect, url_for
                return redirect(url_for('bug.bugtracker'))
                
            except Exception as e:
                # Clean up temporary image files if they were created
                if 'uploads_list' in locals():
                    for upload_info in uploads_list:
                        temp_img_path = upload_info['path']
                        if os.path.exists(temp_img_path):
                            try:
                                os.remove(temp_img_path)
                            except Exception:
                                pass
                return render_template("error.j2", message=f"Issue update failed: {e}")

        # Display edit form
        disp.add_master_layout(
            displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [4, 8], subtitle=f"Edit Issue ID: {issue_id}")
        )
        disp.add_display_item(displayer.DisplayerItemText("Subject"), 0)
        disp.add_display_item(displayer.DisplayerItemInputString("subject", value=issue.subject), 1)
        
        disp.add_master_layout(
            displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [4, 8], subtitle="")
        )
        disp.add_display_item(displayer.DisplayerItemText("Description (supports rich text and images)"), 0)
        # Convert textile description back to HTML for TinyMCE editing
        description_html = redmine_textile_to_html(issue.description, issue)
        disp.add_display_item(displayer.DisplayerItemInputText("description", value=description_html), 1)

        disp.add_master_layout(
            displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12], subtitle="")
        )
        disp.add_display_item(displayer.DisplayerItemButton("update", "Update Issue"))

    # Build the form action URL manually since we need issue_id parameter
    from flask import url_for
    form_action = url_for('bug.edit_issue', issue_id=issue_id)
    return render_template("base_content.j2", content=disp.display(), target=None, form_action=form_action)


def format_description_preview(textile_content, max_length=200):
    """
    Convert Textile description to HTML preview for table display.
    Limits to max_length characters and removes images.
    
    Args:
        textile_content (str): Textile content from Redmine
        max_length (int): Maximum number of characters to display
        
    Returns:
        str: HTML formatted preview
    """
    if not textile_content or not textile_content.strip():
        return ""
    
    # Remove user signatures
    content = re.sub(r'\n*_Added by User.*?_\s*$', '', textile_content, flags=re.MULTILINE | re.DOTALL)
    content = re.sub(r'\n*_Last edited by User.*?_\s*$', '', content, flags=re.MULTILINE | re.DOTALL)
    
    # Remove image references
    content = re.sub(r'!([^!\n]+)!', '', content)
    content = re.sub(r'\[Attached Image: ([^\]]+)\]', '', content)
    content = re.sub(r'\*\[Attached Image: ([^\]]+)\]\*', '', content)
    
    # Convert to HTML
    html = textile.textile(content)
    
    # Strip HTML tags to get plain text for length calculation
    soup = BeautifulSoup(html, 'html.parser')
    text = soup.get_text()
    
    # Truncate if needed
    if len(text) > max_length:
        text = text[:max_length] + "..."
        # Re-convert truncated text to simple HTML
        html = textile.textile(text)
    
    return html


def html_to_redmine_textile(html_content):
    """
    Convert HTML content (from tinymce) to Redmine textile format.
    Handles common formatting and embedded images (base64).
    
    Args:
        html_content (str): HTML content from tinymce editor
        
    Returns:
        tuple: (textile_text, list_of_image_data) where image_data is dict with 'filename' and 'data'
    """
    if not html_content or not html_content.strip():
        return "", []
    
    soup = BeautifulSoup(html_content, 'html.parser')
    images = []
    image_counter = 1
    
    # Extract base64 images and replace with Textile markers
    for img in soup.find_all('img'):
        src = img.get('src', '')
        if isinstance(src, str):
            if src.startswith('data:image'):
                # Extract base64 image data
                match = re.match(r'data:image/([^;]+);base64,(.+)', src)
                if match:
                    img_format = match.group(1)
                    img_data = base64.b64decode(match.group(2))
                    filename = f"image_{image_counter}.{img_format}"
                    images.append({'filename': filename, 'data': img_data})
                    # Replace with a unique marker that we'll convert to textile later
                    img.replace_with(f"__IMAGE_MARKER_{image_counter}__")
                    image_counter += 1
            elif src.startswith('blob:'):
                # Blob URLs are temporary browser URLs that can't be accessed server-side
                img.replace_with("\n[Image - please re-paste or upload]\n")
            elif src.startswith('http'):
                # External image URL - keep as reference
                img.replace_with(f"\n!{src}!\n")
    
    # Convert HTML elements to Textile syntax
    def html_element_to_textile(element):
        """Recursively convert HTML elements to Textile."""
        if isinstance(element, str):
            return element
        
        if element.name is None:
            return str(element)
        
        # Get the text content, recursively processing children
        children_text = ''.join(html_element_to_textile(child) for child in element.children)
        
        # Convert based on tag type
        if element.name in ['strong', 'b']:
            return f"*{children_text}*"
        elif element.name in ['em', 'i']:
            return f"_{children_text}_"
        elif element.name == 'u':
            return f"+{children_text}+"
        elif element.name in ['del', 's', 'strike']:
            return f"-{children_text}-"
        elif element.name == 'h1':
            return f"\n\nh1. {children_text}\n\n"
        elif element.name == 'h2':
            return f"\n\nh2. {children_text}\n\n"
        elif element.name == 'h3':
            return f"\n\nh3. {children_text}\n\n"
        elif element.name == 'h4':
            return f"\n\nh4. {children_text}\n\n"
        elif element.name == 'h5':
            return f"\n\nh5. {children_text}\n\n"
        elif element.name == 'h6':
            return f"\n\nh6. {children_text}\n\n"
        elif element.name == 'code':
            return f"@{children_text}@"
        elif element.name == 'pre':
            return f"\n<pre>\n{children_text}\n</pre>\n"
        elif element.name == 'a':
            href = element.get('href', '')
            if href:
                return f'"{children_text}":{href}'
            return children_text
        elif element.name == 'ul':
            items = []
            for li in element.find_all('li', recursive=False):
                items.append(f"* {html_element_to_textile(li)}")
            return '\n' + '\n'.join(items) + '\n'
        elif element.name == 'ol':
            items = []
            for li in element.find_all('li', recursive=False):
                items.append(f"# {html_element_to_textile(li)}")
            return '\n' + '\n'.join(items) + '\n'
        elif element.name == 'li':
            # For nested lists, just return the content
            return children_text
        elif element.name == 'p':
            return f"\n{children_text}\n"
        elif element.name == 'br':
            return "\n"
        elif element.name == 'div':
            return f"\n{children_text}\n"
        else:
            # Unknown tags - just return the text content
            return children_text
    
    # Convert the entire body to Textile
    textile = html_element_to_textile(soup)
    
    # Replace image markers with proper Textile syntax
    for i in range(1, image_counter):
        textile = textile.replace(f"__IMAGE_MARKER_{i}__", f"\n!image_{i}.png!\n")
    
    # Clean up excessive newlines
    textile = re.sub(r'\n{3,}', '\n\n', textile)
    
    return textile.strip(), images


def redmine_textile_to_html(textile_content, issue=None):
    """
    Convert Redmine textile format to HTML for editing in TinyMCE.
    Uses the textile library for proper conversion.
    Optionally fetches image attachments from Redmine and embeds as base64.
    
    Args:
        textile_content (str): Textile content from Redmine
        issue: Optional Redmine issue object to fetch attachments from
        
    Returns:
        str: HTML content for TinyMCE
    """
    if not textile_content or not textile_content.strip():
        return ""
    
    # Remove user signature lines FIRST (before conversion)
    content = re.sub(r'\n*_Added by User.*?_\s*$', '', textile_content, flags=re.MULTILINE | re.DOTALL)
    content = re.sub(r'\n*_Last edited by User.*?_\s*$', '', content, flags=re.MULTILINE | re.DOTALL)
    
    # If we have the issue object, try to replace image references with base64 embedded images
    if issue and hasattr(issue, 'attachments'):
        try:
            # Create a mapping of all image attachments
            attachment_map = {}
            for attachment in issue.attachments:
                # Check if it's an image
                if attachment.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp')):
                    attachment_map[attachment.filename] = attachment
            
            # Find all image references - both Textile format (!filename!) and our placeholder format
            # Pattern 1: !filename! (Textile format)
            image_refs = re.findall(r'!([^!\n]+)!', content)
            # Pattern 2: [Attached Image: filename] or *[Attached Image: filename]* (our placeholder)
            placeholder_refs = re.findall(r'\[Attached Image: ([^\]]+)\]', content)
            
            all_refs = list(set(image_refs + placeholder_refs))  # Combine and deduplicate
            
            for img_ref in all_refs:
                # Try to find matching attachment
                if img_ref in attachment_map:
                    attachment = attachment_map[img_ref]
                    try:
                        # Download the attachment
                        img_response = attachment.download()
                        # The download() method returns a Response object, we need to get the content
                        if hasattr(img_response, 'content'):
                            img_data = img_response.content
                        elif hasattr(img_response, 'read'):
                            img_data = img_response.read()
                        else:
                            img_data = img_response
                        # Convert to base64
                        img_base64 = base64.b64encode(img_data).decode('utf-8')
                        # Determine image type
                        ext = attachment.filename.lower().split('.')[-1]
                        if ext == 'jpg':
                            ext = 'jpeg'
                        mime_type = f'image/{ext}'
                        # Create HTML img tag with base64
                        img_tag = f'<img src="data:{mime_type};base64,{img_base64}" alt="{attachment.filename}"/>'
                        
                        # Replace ALL occurrences of this image reference
                        content = content.replace(f'!{img_ref}!', img_tag)
                        content = content.replace(f'[Attached Image: {img_ref}]', img_tag)
                        content = content.replace(f'*[Attached Image: {img_ref}]*', img_tag)
                    except Exception:
                        # If download fails for this specific image, leave it as placeholder
                        pass
        except Exception:
            # If image fetching fails, just continue with placeholders
            pass
    
    # Replace any remaining image references with placeholders
    content = re.sub(r'!([^!\n]+)!', r'*[Attached Image: \1]*', content)
    
    # Use the textile library to convert to HTML
    html = textile.textile(content)
    
    return html.strip()


def create_logs_archive(max_lines=500):
    """
    Create a zip archive containing the last N lines from each log file.
    
    Args:
        max_lines (int): Maximum number of lines to extract from each log file
        
    Returns:
        str: Path to the created zip file, or None if no logs found
    """
    logs_dir = os.path.join(os.getcwd(), "logs")
    if not os.path.exists(logs_dir):
        return None
    
    # Create a temporary zip file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_path = os.path.join(os.getcwd(), f"logs_archive_{timestamp}.zip")
    
    log_files = glob.glob(os.path.join(logs_dir, "*.log"))
    if not log_files:
        return None
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for log_file in log_files:
            try:
                # Read last N lines from the log file
                with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                    # Read all lines and get the last max_lines
                    lines = f.readlines()
                    last_lines = lines[-max_lines:] if len(lines) > max_lines else lines
                
                # Create a temporary file name for the archive
                log_filename = os.path.basename(log_file)
                temp_content = f"=== Last {len(last_lines)} lines from {log_filename} ===\n\n"
                temp_content += ''.join(last_lines)
                
                # Write to zip
                zipf.writestr(log_filename, temp_content)
            except Exception:
                # If one log fails, continue with others
                continue
    
    return zip_path if os.path.exists(zip_path) else None


@bp.route("/bugtracker", methods=["GET", "POST"])
def bugtracker():
    settings_mgr = get_settings_manager()
    disp = displayer.Displayer()
    # disp.add_generic("Changelog", display=False)
    User_defined_module.User_defined_module.m_default_name = "Bug Tracker"
    disp.add_module(User_defined_module.User_defined_module)

    if site_conf.site_conf_obj and not site_conf.site_conf_obj.m_globals["on_target"]:
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        # Get Redmine configuration with error handling
        configs, error = get_config_or_error(settings_mgr, 
                                             "redmine.address.value",
                                             "redmine.user.value",
                                             "redmine.password.value")
        if error:
            return error

        try:
            redmine = Redmine(
                configs["redmine.address.value"], 
                username=configs["redmine.user.value"], 
                password=configs["redmine.password.value"], 
                requests={"verify": False}
            )
        except Exception as e:
            return render_template("error.j2", message=f"Redmine connection failed with the following message: {e}")
        
        if site_conf.site_conf_obj:
            project_id = site_conf.site_conf_obj.m_app["name"].lower().replace('_', '-').replace(' ', '-')
            version_name = site_conf.site_conf_obj.m_app["version"].lower().replace('_', '-').replace(' ', '-')
            
            # Verify project exists and fetch data
            try:
                # Test if project exists by fetching it
                project = redmine.project.get(project_id)
                issues = redmine.issue.filter(project_id=project_id)
                issues_closed = redmine.issue.filter(project_id=project_id, status_id=5)
                issues_rejected = redmine.issue.filter(project_id=project_id, status_id=6)
                versions = redmine.version.filter(project_id=project_id)
            except redminelib.exceptions.ResourceNotFoundError:
                return render_template("error.j2", message=f"Project '{project_id}' was not found in Redmine. Please check your configuration.")
            except Exception as e:
                return render_template("error.j2", message=f"Error fetching project data from Redmine: {e}")
        else:
            # Not on target, variables remain uninitialized
            project_id = None
            issues = []
            issues_closed = []
            issues_rejected = []
            versions = []
            version_name = ""

        if request.method == "POST":
            data_in = utilities.util_post_to_json(request.form.to_dict())["Bug Tracker"]
            if len(data_in.get("description", "")) < 5:
                return render_template("error.j2", message="Please provide a meaningful description of the issue")
            if len(data_in.get("subject", "")) < 5:
                return render_template("error.j2", message="Please provide a meaningful subject of the issue")

            # Convert HTML description to Redmine textile format
            description_html = data_in.get("description", "")
            description_textile, embedded_images = html_to_redmine_textile(description_html)

            # Check if version exists, create if it doesn't
            version_redmine = 0
            version_found = False
            for version in versions:
                if version.name == version_name:
                    version_redmine = version.id
                    version_found = True
                    break
            
            # Create version if it doesn't exist
            if not version_found and version_name:
                try:
                    new_version = redmine.version.create(
                        project_id=project_id,
                        name=version_name
                    )
                    version_redmine = new_version.id
                    # Refresh versions list
                    versions = redmine.version.filter(project_id=project_id)
                except Exception as e:
                    return render_template("error.j2", message=f"Failed to create version '{version_name}' in Redmine: {e}")

            log_archive_path = None
            try:
                current_user = "GUEST"
                if auth_manager:
                    current_user = auth_manager.get_current_user() or "GUEST"
                
                # Create logs archive
                try:
                    log_archive_path = create_logs_archive(max_lines=500)
                except Exception:
                    pass  # Continue without logs if archive creation fails
                
                uploads_list = []
                
                # Add log archive
                if log_archive_path and os.path.exists(log_archive_path):
                    uploads_list.append({'path': log_archive_path, 'description': 'Application logs archive'})
                
                # Add embedded images from description
                for img_data in embedded_images:
                    # Save image temporarily
                    temp_img_path = os.path.join(os.getcwd(), img_data['filename'])
                    with open(temp_img_path, 'wb') as f:
                        f.write(img_data['data'])
                    uploads_list.append({'path': temp_img_path, 'description': f"Embedded image: {img_data['filename']}"})
                
                if 'redmine' in locals():
                    issue_data = {
                        'subject': data_in["subject"],
                        'description': description_textile + '\r\n\r\n' + f"_Added by User {current_user}_",
                        'project_id': project_id,
                        'custom_fields': [
                            {"id": 10, "value": version_redmine}, 
                            {"id": 11, "value": "-"}, 
                            {"id": 16, "value": "-"}, 
                            {"id": 20, "value": "-"}
                        ]
                    }
                    
                    # Only add uploads if we have files
                    if uploads_list:
                        issue_data['uploads'] = uploads_list
                    
                    redmine.issue.create(**issue_data)
                    
                    # Clean up temporary files
                    if log_archive_path and os.path.exists(log_archive_path):
                        try:
                            os.remove(log_archive_path)
                        except Exception:
                            pass  # Ignore cleanup errors
                    
                    # Clean up temporary image files
                    for img_data in embedded_images:
                        temp_img_path = os.path.join(os.getcwd(), img_data['filename'])
                        if os.path.exists(temp_img_path):
                            try:
                                os.remove(temp_img_path)
                            except Exception:
                                pass
                            
            except Exception as e:
                # Clean up temporary files in case of error
                if log_archive_path and os.path.exists(log_archive_path):
                    try:
                        os.remove(log_archive_path)
                    except Exception:
                        pass
                
                # Clean up temporary image files
                for img_data in embedded_images:
                    temp_img_path = os.path.join(os.getcwd(), img_data['filename'])
                    if os.path.exists(temp_img_path):
                        try:
                            os.remove(temp_img_path)
                        except Exception:
                            pass
                
                return render_template("error.j2", message=f"Issue creation failed with the following message: {e}")

        disp.add_master_layout(
            displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [4, 8], subtitle="Create a new issue")
        )
        disp.add_display_item(displayer.DisplayerItemText("Enter subject"), 0)
        disp.add_display_item(displayer.DisplayerItemInputString("subject"), 1)
        disp.add_master_layout(
            displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [4, 8], subtitle="")
        )
        disp.add_display_item(displayer.DisplayerItemText("Enter Description (supports rich text and images)"), 0)
        disp.add_display_item(displayer.DisplayerItemInputText("description"), 1)

        disp.add_master_layout(
            displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12], subtitle="")
        )
        disp.add_display_item(displayer.DisplayerItemButton("create", "Submit"))

        # Display current issues in a table
        disp.add_master_layout(
            displayer.DisplayerLayout(
                displayer.Layouts.TABLE,
                [
                    "#",
                    "Status",
                    "Subject",
                    "Description",
                    "Updated Time",
                    "Actions"
                ],
                subtitle="Current issues",
            )
        )

        for index, issue in enumerate(issues, start=1):
            disp.add_display_item(displayer.DisplayerItemText(str(issue.id)), column=0, line=index)
            disp.add_display_item(displayer.DisplayerItemText(issue.status.name), column=1, line=index)
            disp.add_display_item(displayer.DisplayerItemText(issue.subject), column=2, line=index)
            # Convert Textile to HTML and limit to 200 characters
            description_html = format_description_preview(issue.description, max_length=200)
            disp.add_display_item(displayer.DisplayerItemText(f'<div style="max-width:40vw; white-space:normal; word-break:break-word;">{description_html}</div>'), column=3, line=index)
            disp.add_display_item(displayer.DisplayerItemText(issue.updated_on.strftime("%Y-%m-%d %H:%M:%S")), column=4, line=index)
            disp.add_display_item(
                displayer.DisplayerItemActionButtons(
                    id=f"issue_{issue.id}_actions",
                    view_url=issue.url,
                    edit_url=f"/bug/edit/{issue.id}"
                ),
                column=5,
                line=index
            )

        # Display closed issues in a table
        disp.add_master_layout(
            displayer.DisplayerLayout(
                displayer.Layouts.TABLE,
                [
                    "#",
                    "Status",
                    "Subject",
                    "Description",
                    "Updated Time",
                    "Actions"
                ],
                subtitle="Closed issues",
            )
        )

        for index, issue in enumerate(issues_closed, start=1):  # Replace issues_open with the desired issue list
            disp.add_display_item(displayer.DisplayerItemText(str(issue.id)), column=0, line=index)
            disp.add_display_item(displayer.DisplayerItemText(issue.status.name), column=1, line=index)
            disp.add_display_item(displayer.DisplayerItemText(issue.subject), column=2, line=index)
            # Convert Textile to HTML and limit to 200 characters
            description_html = format_description_preview(issue.description, max_length=200)
            disp.add_display_item(displayer.DisplayerItemText(f'<div style="max-width:40vw; white-space:normal; word-break:break-word;">{description_html}</div>'), column=3, line=index)
            # Use updated_on if closed_on is not available
            closed_time = issue.closed_on.strftime("%Y-%m-%d %H:%M:%S") if hasattr(issue, 'closed_on') and issue.closed_on else issue.updated_on.strftime("%Y-%m-%d %H:%M:%S")
            disp.add_display_item(displayer.DisplayerItemText(closed_time), column=4, line=index)
            disp.add_display_item(
                displayer.DisplayerItemActionButtons(
                    id=f"closed_issue_{issue.id}_actions",
                    view_url=issue.url
                ),
                column=5,
                line=index
            )

        # Display rejected issues in a table
        disp.add_master_layout(
            displayer.DisplayerLayout(
                displayer.Layouts.TABLE,
                [
                    "#",
                    "Status",
                    "Subject",
                    "Description",
                    "Updated Time",
                    "Actions"
                ],
                subtitle="Rejected issues",
            )
        )

        for index, issue in enumerate(issues_rejected, start=1):  # Replace issues_open with the desired issue list
            disp.add_display_item(displayer.DisplayerItemText(str(issue.id)), column=0, line=index)
            disp.add_display_item(displayer.DisplayerItemText(issue.status.name), column=1, line=index)
            disp.add_display_item(displayer.DisplayerItemText(issue.subject), column=2, line=index)
            # Convert Textile to HTML and limit to 200 characters
            description_html = format_description_preview(issue.description, max_length=200)
            disp.add_display_item(displayer.DisplayerItemText(f'<div style="max-width:40vw; white-space:normal; word-break:break-word;">{description_html}</div>'), column=3, line=index)
            # Use updated_on if closed_on is not available
            closed_time = issue.closed_on.strftime("%Y-%m-%d %H:%M:%S") if hasattr(issue, 'closed_on') and issue.closed_on else issue.updated_on.strftime("%Y-%m-%d %H:%M:%S")
            disp.add_display_item(displayer.DisplayerItemText(closed_time), column=4, line=index)
            disp.add_display_item(
                displayer.DisplayerItemActionButtons(
                    id=f"rejected_issue_{issue.id}_actions",
                    view_url=issue.url
                ),
                column=5,
                line=index
            )

    return render_template("base_content.j2", content=disp.display(), target="bug.bugtracker")
