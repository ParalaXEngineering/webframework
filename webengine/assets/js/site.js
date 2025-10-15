function cascaded(data, ids, caller)
{
    // Find the level
    var level = ids.indexOf(caller.id)
    if(level >= 0 && level < ids.length)
    {
        //Start by clearing all the following levels
        for(var i = level + 1; i < ids.length; i++)
        {
            toclear = document.getElementById(ids[i])
            while (toclear.options.length > 0) {                
                toclear.remove(0);
            }
        }   

        var selected = document.getElementById(ids[level]).value
        var toUpdate = document.getElementById(ids[level + 1])

        console.log(selected)
        console.log(toUpdate)
        console.log(ids)

        // Recover the data for the given level
        var data_to_parse = data
        for(var i = 0; i <= level; i++)
        {
            console.log("-----")
            console.log(i)
            previous_selection = document.getElementById(ids[i]).value
            console.log(previous_selection)
            data_to_parse = data_to_parse[previous_selection]
            console.log(data_to_parse)
        }
    
        // Handle both objects (get keys) and arrays (use array items directly)
        var data_to_option = Array.isArray(data_to_parse) ? data_to_parse : Object.keys(data_to_parse)
        console.log(data_to_option)
        toUpdate.add(new Option("", ""))
        for (var element of data_to_option) {
            toUpdate.add(new Option(element, element))
        }
        toUpdate.value
        
    }
}

function setting_add_list(name)
{
    console.log(name)

    // If the first item in the list is hidden, then it's simply a matter of displaying it
    var list0 = document.getElementById(name + ".masked");
    if (list0 && list0.style.display == 'none') 
    {
        list0.id = name + ".list0"
        list0.name = name + ".list0"
        document.getElementById(name + ".list0").value = "";
        list0.style.display = ''
        return
    }


     //Find the biggest line
     var max_nb = 0
     var content_name = []
     for (var i = 0; i < 100; i++)
     {
         var div = document.getElementById(name + ".list" + (i).toString());
         if(div)
         {
            console.log(div)
            content_name.push(document.getElementById(name + ".list" + (i).toString()).value);
            max_nb += 1;
         }
         else
         {
             i = 100;
         }
     }

     console.log(content_name)
 
     //Add the line
     var div = document.getElementById(name + ".div")
     content = document.getElementById(name + ".list0").outerHTML;
     content = content.replaceAll("list0", "list" + (max_nb).toString());
     div.innerHTML += content

     //Remove the content of what we pushed
     document.getElementById(name + ".list" + (max_nb).toString()).value = ""
 
     //And repush the user data
     for (var i = 0; i < max_nb; i++)
     {
         document.getElementById(name + ".list" + (i).toString()).value = content_name[i];
     }   
}

function setting_rm_list(name)
{
    console.log(name)

     //Find the biggest line
     var max_nb = 0
     var content_name = []
     for (var i = 0; i < 100; i++)
     {
         var div = document.getElementById(name + ".list" + (i).toString());
         if(div)
         {
            console.log(div)
            content_name.push(document.getElementById(name + ".list" + (i).toString()).value);
            max_nb += 1;
         }
         else
         {
             i = 100;
         }
     }

     
     if(max_nb == 1)
     {
        var div = document.getElementById(name + ".list0")
        div.style.display = 'none'; // Cache le div
        div.id = name + ".masked"
        div.name = ""
     }
     else
     {
        var div = document.getElementById(name + ".div")
        document.getElementById(name + ".list" + (max_nb - 1).toString()).remove();
     }

     settings_list_format(name)
}

function button_machine_display(info)
{
    var div = document.getElementById("btn-info")
    div.innerHTML = info
}

function setting_add_mapping(name)
{
    // If the first item in the list is hidden, then it's simply a matter of displaying it
    var maprow0 = document.getElementById(name + ".masked");
    if (maprow0 && maprow0.style.display == 'none') 
    {
        maprow0.id = name + ".maprow0"
        maprow0.name = name + ".maprow0"
        document.getElementById(name + ".maprow0").value = "";
        maprow0.style.display = ''
        return
    }

     //Find the biggest line
     var max_nb = 0
     var content_left = []
     var content_right = []
     for (var i = 0; i < 100; i++)
     {
         var div = document.getElementById(name + ".mapleft" + (i).toString());
         if(div)
         {
             content_left.push(document.getElementById(name + ".mapleft" + (i).toString()).value);
             content_right.push(document.getElementById(name + ".mapright" + (i).toString()).value);
             max_nb += 1;
         }
         else
         {
             i = 100;
         }
     }
 
     //Add the line
     var div = document.getElementById(name + ".div")
     content = document.getElementById(name + ".maprow0").outerHTML;
     console.log(name + ".maprow0")
     content = content.replaceAll("0", (max_nb).toString());
     div.innerHTML += content

     console.log(content_left)
     console.log(content_right)

     //Remove the content of what we pushed
     document.getElementById(name + ".mapleft" + (max_nb).toString()).value = ""
     document.getElementById(name + ".mapright" + (max_nb).toString()).value = ""
 
     //And repush the user data
     for (var i = 0; i < max_nb; i++)
     {
         document.getElementById(name + ".mapleft" + (i).toString()).value = content_left[i];
         document.getElementById(name + ".mapright" + (i).toString()).value = content_right[i];
     }   
}

function setting_rm_mapping(name)
{
     //Find the biggest line
     var max_nb = 0
     var content_left = []
     var content_right = []
     for (var i = 0; i < 100; i++)
     {
         var div = document.getElementById(name + ".mapleft" + (i).toString());
         if(div)
         {
             content_left.push(document.getElementById(name + ".mapleft" + (i).toString()).value);
             content_right.push(document.getElementById(name + ".mapright" + (i).toString()).value);
             max_nb += 1;
         }
         else
         {
             i = 100;
         }
     }

    if(max_nb == 1)
    {
        var div = document.getElementById(name + ".maprow0")
        div.style.display = 'none'; // Cache le div
        div.id = name + ".masked"
        div.name = ""
    }
    else
    {
        var div = document.getElementById(name + ".div")
        document.getElementById(name + ".mapleft" + (max_nb - 1).toString()).remove();
        document.getElementById(name + ".mapright" + (max_nb - 1).toString()).remove();
    } 
}

function settings_list_format(name)
{
    //Find the biggest line
    var content_name = []
    for (var i = 0; i < 100; i++)
    {
        var div = document.getElementById(name + ".list" + (i).toString());
        if(div)
        {
            content_name.push(document.getElementById(name + ".list" + (i).toString()).value);
        }
        else
        {
            i = 100;
        }
    }

    //Create the result
    document.getElementById(name).value = content_name.filter(Boolean).join('#')
}

function settings_map_format(name)
{
    //Find the biggest line
    var content_left = []
    var content_right = []
    for (var i = 0; i < 100; i++)
    {
        var div = document.getElementById(name + ".maprow" + (i).toString());
        if(div)
        {
            content_left.push(document.getElementById(name + ".mapleft" + (i).toString()).value);
            content_right.push(document.getElementById(name + ".mapright" + (i).toString()).value);
        }
        else
        {
            i = 100;
        }
    }

    //Create the result
    var content = {}
    for (var i = 0; i < content_left.length; i++)
    {
        content[content_left[i]] = content_right[i]
    }
    document.getElementById(name).value = JSON.stringify(content)
}

document.addEventListener('DOMContentLoaded', (event) => {
    // Focus order on enter
    const focusables = [...document.querySelectorAll('.focusable')];

    focusables.forEach((el, idx) => {
        el.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            const next = focusables[idx + 1];
            if (next) {
            next.focus();
            } else {
            el.blur(); // optional: remove focus on last element
            }
        }
        });
    });

    document.addEventListener('keydown', function (event) {
        if (event.key === 'Enter') {
            const isFocusable = event.target.classList.contains('focusable');

            // If not focusable, block Enter to prevent accidental submit
            if (!isFocusable) {
                event.preventDefault();
            }
            // If focusable and it's a button, manually trigger click
            else if (event.target.tagName === 'BUTTON') {
                event.preventDefault();
                event.target.click();
            }
        }
    });

    // Sélection de la checkbox
    const toggleCheckbox = document.getElementById('toggle-dark');

    // Ajout de l'écouteur d'événements sur la checkbox
    toggleCheckbox.addEventListener('change', function() {
        // Sélection de tous les éléments avec la classe 'bg-light' ou 'bg-dark'
        const elements = document.querySelectorAll('.bg-light, .bg-body');

        // Parcourir chaque élément et changer sa classe
        elements.forEach(element => {
            if (element.classList.contains('bg-light')) {
                element.classList.replace('bg-light', 'bg-body');
            } else {
                element.classList.replace('bg-body', 'bg-light');
            }
        });
    });

});

function scrollToBottom() {
    var terminalConsole = document.getElementById("terminal-console");
    terminalConsole.scrollTop = terminalConsole.scrollHeight;
}


function send_terminal() {
    var socket = io.connect('http://' + document.domain + ':' + location.port);
    var inputElement = document.getElementById('terminal_input'); // C'est l'élément d'input lui-même
    var command = inputElement.value; // C'est la valeur de l'input
    socket.emit('terminal_cmd', command);
    inputElement.value = ""; // Réinitialisez l'élément d'input ici
    
    // Créez une instance de MutationObserver pour surveiller les changements dans le terminal
    var observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.addedNodes.length) {
                scrollToBottom();
            }
        });
    });

    // Configuration de l'observer :
    var config = { childList: true };

    // Ciblez l'élément à observer :
    var target = document.getElementById('terminal-user-content');

    // Commencez à observer le target pour les mutations configurées
    observer.observe(target, config);
}

function saveScrollPosition() {
    var scrollPosition = window.pageYOffset || document.documentElement.scrollTop;
    localStorage.setItem('scrollPosition', scrollPosition);
    // Soumettre le formulaire ou faire l'appel AJAX ici
    document.getElementById('your-form-id').submit();
}

$(document).ready(function() {
    console.log('[DEBUG] site.js loaded and document ready');
    console.log('[DEBUG] Attempting to connect to SocketIO at:', 'http://' + document.domain + ':' + location.port);
    
    // Make socket globally accessible for other scripts
    window.socket = io.connect('http://' + document.domain + ':' + location.port);
    var socket = window.socket;  // Keep local reference for compatibility
    
    // Debug: Socket connection events
    socket.on('connect', function() {
        console.log('[SOCKETIO] Connected to server');
    });
    
    socket.on('disconnect', function() {
        console.log('[SOCKETIO] Disconnected from server');
    });
    
    socket.on('connect_error', function(error) {
        console.error('[SOCKETIO] Connection error:', error);
    });
    
    setTimeout(test_connect, 1000)
    function test_connect(){
        console.log('[SOCKETIO] Emitting user_connected');
        socket.emit("user_connected");
    }

    // Append overlay to body
    $('body').append(`
        <div id="overlay" style="
            display: none;
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            background: rgba(0, 0, 0, 0.8);
            z-index: 9999;
            justify-content: center;
            align-items: center;
            ">
            <img src="" style="max-width: 90%; max-height: 90%; box-shadow: 0 0 15px #000;">
        </div>
    `);

    $('.zoomable').click(function() {
        var imageSrc = $(this).attr('src');
        $('#overlay img').attr('src', imageSrc);
        $('#overlay').css('display', 'flex').hide().fadeIn(200);
    });

    $('#overlay').click(function() {
        $('#overlay').fadeOut(200);
    });
    // Tooltips in selects
    $('select').each(function() {
        var select = $(this);

        function addTooltipText() {
            select.find('option').each(function() {
                var option = $(this);
                var tooltip = option.data('tooltip');
                if (tooltip && !option.data('original-text')) {
                    var value = option.val();
                    option.data('original-text', option.text());
                    option.text(value + ' - ' + tooltip);
                }
            });
        }

        function removeTooltipText() {
            select.find('option').each(function() {
                var option = $(this);
                var originalText = option.data('original-text');
                if (originalText) {
                    option.text(originalText);
                    option.removeData('original-text');
                }
            });
        }

        select.on('focus', function() {
            addTooltipText();
        });

        select.on('blur', function() {
            removeTooltipText();
        });
    });

    // Restore scroll position
    window.onload = function() {
        var scrollPosition = localStorage.getItem('scrollPosition');
        if (scrollPosition) {
            window.scrollTo(0, scrollPosition);
            localStorage.removeItem('scrollPosition');
        }
    };

    // Update top bar
    socket.on( 'content', function( msg ) {
        for(let id of Object.keys(msg))
        {
            let div = document.getElementById(id + "_content")
            if(div)
                div.innerHTML = msg[id]
        }
    })

    socket.on('threads', function(msg) 
    {
        let content = ""
        if(msg.length == 0)
        {
            content = "No running task"
        }
        else
        {
            for(var i = 0; i < msg.length; i++)
            {
                if(msg[i]["state"] == -1)
                {
                    content += '<div class="row"><div class="col-6">' + msg[i]["name"].replace(" ", "_") + '</div><div class="col-6"><div class="spinner-border spinner-border-sm text-primary" role="status"></div></div></div>'
                }
                else
                {
                    content += '<div class="row">  <div class="col-6">' + msg[i]["name"].replace(" ", "_") + '</div> <div class="col-6">' + msg[i]["state"] + '%</div>  </div>'
                }
            }
        }

        let div = document.getElementById("thread_run")
        if(div)
        {
            div.innerHTML = content
        }
    })
    socket.on( 'reload', function( msg ) {
        console.log("[SOCKET] Received reload event:", msg["id"], "content length:", msg["content"].length);
        let div = document.getElementById(msg["id"])
        console.log("[SOCKET] Target div found:", div !== null);
        if(div) {
            smartUpdateContent(div, msg["content"]);
        }

        // When any image with class 'zoomable' is clicked
        $('.zoomable').click(function() {
            var imageSrc = $(this).attr('src');
            $('#overlay img').attr('src', imageSrc);
            $('#overlay').fadeIn();
        });

        // When overlay is clicked
        $('#overlay').click(function() {
            $('#overlay').fadeOut();
        });
    })
    
    /**
     * Smart content update - only updates DOM elements that changed
     * Preserves state like active tabs, scroll position, user interactions
     */
    function smartUpdateContent(element, newHtmlString) {
        console.log("[SMART_UPDATE] Called for element:", element.id, "current children:", element.childNodes.length);
        // Create temporary container with new content
        const temp = document.createElement('div');
        temp.innerHTML = newHtmlString;
        
        // If element is currently empty, just set innerHTML
        if (!element.firstChild) {
            console.log("[SMART_UPDATE] Element empty, setting innerHTML directly");
            element.innerHTML = newHtmlString;
            return;
        }
        
        // STEP 1: Find all currently active tabs/content BEFORE updating
        const activeStates = new Map();
        element.querySelectorAll('[role="tab"][aria-selected="true"]').forEach(tab => {
            const tabId = tab.getAttribute('id');
            const targetId = tab.getAttribute('data-bs-target') || tab.getAttribute('href');
            if (tabId) {
                activeStates.set(tabId, targetId);
            }
        });
        
        // STEP 2: Compare children of old and new
        const oldChildren = Array.from(element.childNodes);
        const newChildren = Array.from(temp.childNodes);
        
        // Update or replace children
        const maxLength = Math.max(oldChildren.length, newChildren.length);
        for (let i = 0; i < maxLength; i++) {
            if (i >= newChildren.length) {
                element.removeChild(oldChildren[i]);
            } else if (i >= oldChildren.length) {
                element.appendChild(newChildren[i].cloneNode(true));
            } else {
                if (nodesAreSimilar(oldChildren[i], newChildren[i])) {
                    updateNode(oldChildren[i], newChildren[i]);
                } else {
                    element.replaceChild(newChildren[i].cloneNode(true), oldChildren[i]);
                }
            }
        }
        
        // STEP 3: Restore active states AFTER updating
        activeStates.forEach((targetId, tabId) => {
            const tab = element.querySelector(`#${CSS.escape(tabId)}`);
            const target = element.querySelector(targetId?.replace('#', '#'));
            
            if (tab && target) {
                // Deactivate all tabs in this group first
                const tabList = tab.closest('[role="tablist"]');
                if (tabList) {
                    tabList.querySelectorAll('[role="tab"]').forEach(t => {
                        t.classList.remove('active');
                        t.setAttribute('aria-selected', 'false');
                    });
                }
                
                // Deactivate all tab panes in this group
                const tabContent = target.parentElement;
                if (tabContent?.classList.contains('tab-content')) {
                    tabContent.querySelectorAll('.tab-pane').forEach(pane => {
                        pane.classList.remove('active', 'show');
                    });
                }
                
                // Activate the preserved tab
                tab.classList.add('active');
                tab.setAttribute('aria-selected', 'true');
                target.classList.add('active', 'show');
            }
        });
    }
    
    /**
     * Recursively compare and update DOM nodes
     */
    function updateNode(oldNode, newNode) {
        // Get children as arrays
        const oldChildren = Array.from(oldNode.childNodes);
        const newChildren = Array.from(newNode.childNodes);
        
        // Handle text nodes
        if (oldNode.nodeType === Node.TEXT_NODE && newNode.nodeType === Node.TEXT_NODE) {
            if (oldNode.textContent !== newNode.textContent) {
                oldNode.textContent = newNode.textContent;
            }
            return;
        }
        
        // Handle element nodes
        if (oldNode.nodeType === Node.ELEMENT_NODE && newNode.nodeType === Node.ELEMENT_NODE) {
            // Update attributes if changed
            updateAttributes(oldNode, newNode);
            
            // Update children
            const maxLength = Math.max(oldChildren.length, newChildren.length);
            
            for (let i = 0; i < maxLength; i++) {
                const oldChild = oldChildren[i];
                const newChild = newChildren[i];
                
                if (!oldChild && newChild) {
                    oldNode.appendChild(newChild.cloneNode(true));
                } else if (oldChild && !newChild) {
                    oldNode.removeChild(oldChild);
                } else if (oldChild && newChild) {
                    if (nodesAreSimilar(oldChild, newChild)) {
                        updateNode(oldChild, newChild);
                    } else {
                        oldNode.replaceChild(newChild.cloneNode(true), oldChild);
                    }
                }
            }
        }
    }
    
    /**
     * Check if two nodes are similar enough to update in place
     */
    function nodesAreSimilar(node1, node2) {
        // Same node type
        if (node1.nodeType !== node2.nodeType) return false;
        
        // Text nodes are always similar
        if (node1.nodeType === Node.TEXT_NODE) return true;
        
        // Element nodes: same tag name
        if (node1.nodeType === Node.ELEMENT_NODE) {
            if (node1.tagName !== node2.tagName) return false;
            
            // Prefer to update nodes with same ID
            const id1 = node1.getAttribute('id');
            const id2 = node2.getAttribute('id');
            if (id1 && id2) {
                return id1 === id2;
            }
            
            // Same tag is good enough for most cases
            return true;
        }
        
        return false;
    }
    
    /**
     * Update element attributes if they changed
     */
    function updateAttributes(oldElement, newElement) {
        // Get all attribute names from both elements
        const oldAttrs = oldElement.attributes;
        const newAttrs = newElement.attributes;
        
        // Update/add new attributes - just sync them directly
        // Tab state preservation is handled at higher level in smartUpdateContent
        for (let attr of newAttrs) {
            const oldValue = oldElement.getAttribute(attr.name);
            const newValue = attr.value;
            
            if (attr.name === 'class') {
                const finalClasses = newValue;
                if (oldElement.className !== finalClasses) {
                    oldElement.className = finalClasses;
                }
            } else if (oldValue !== newValue) {
                // Update other attributes that changed
                oldElement.setAttribute(attr.name, newValue);
            }
        }
        
        // Remove attributes that no longer exist
        for (let attr of oldAttrs) {
            if (!newElement.hasAttribute(attr.name)) {
                oldElement.removeAttribute(attr.name);
            }
        }
    }

    socket.on( 'result', function( msg ) {
        let div = document.getElementById("progress_result")
        if(div)
            div.innerHTML = '<div class="alert alert-' + msg["category"] + '">' + msg["text"] + '</div>'
    })

    socket.on( 'modal', function( msg ) {
        let div = document.getElementById(msg["id"] + "_content")
        if(div)
            div.innerHTML = msg["text"]
    })

    socket.on( 'popup', function( msg ) {
        console.log('[SOCKETIO] Received popup:', msg);
        for(let level of Object.keys(msg))
        {
            console.log('[SOCKETIO] Popup level:', level, 'Content:', msg[level]);
            if(level != 4)
            {
                Swal.fire({
                    html:  msg[level],
                    icon: level,
                    confirmButtonText: 'Ok'
                })
            }
            else
            {
                Swal.fire({
                    html:  msg[level],
                    confirmButtonText: 'Ok'
                })
            }
        }
    })

    socket.on( 'button', function( msg ) {
        for(let id of Object.keys(msg))
        {
            let div = document.getElementById(id)
            if(div)
                // div.outerHTML = '<button class="mx-1 btn btn-' + msg[id][2] + '" id="' + id + '"><h2><i class="mdi mdi-' + msg[id][0] + ' text-light mx-1"></i></h2>' + msg[id][1] + '</button>'
                if (id == "ppu_stat" || id == "hmi_stat")
                    div.outerHTML = '<button class="mx-1 btn btn-' + msg[id][2] + '" id="' + id + '"><h2><i class="mdi mdi-' + msg[id][0] + ' text-light mx-1"></i></h2>' + msg[id][1] + '</button>'
                else
                div.outerHTML = '<button class="mx-1 btn btn-' + msg[id][2] + '" id="' + id + '" style="font-size: 0.7em; margin-top: 0; margin-bottom: 0; padding-top: 0; padding-bottom: 0;"><i class="mdi mdi-' + msg[id][0] + ' text-light mx-1" style="font-size: 2em; margin: 0; padding: 0;"><br></i>' + msg[id][1] + '</button>'
        }
    })

    socket.on( 'enable_button', function( msg ) {
        for(var i = 0; i < msg.length; i++)
        {
            let button = document.getElementById(msg[i])
            console.log(button)
            if(button)
                button.classList.remove("disabled")
        }
    })

    socket.on( 'disable_button', function( msg ) {
        for(var i = 0; i < msg.length; i++)
        {
            console.log(msg[i])
            let button = document.getElementById(msg[i])
            button.classList.add("disabled")
        }
    })

    socket.on( 'action_status', function( msg ) {
        console.log('[SOCKETIO] Received action_status:', msg);
        for(let category of Object.keys(msg))
        {
            console.log('[SOCKETIO] Processing category:', category, 'Message:', msg[category]);
            //Do we already have the status in the table
            let current_status = document.getElementById(msg[category][0])
            if(!current_status)
            {
                let table = document.getElementById(category + "_result")
                console.log(category)
                console.log('[SOCKETIO] Table element:', table);
                //Prepare the cell
                let status = '<div id="' + msg[category][0] + '"></div></div>'

                if(table)
                {
                    row = table.insertRow()
                    cell = row.insertCell(0)
                    cell.innerHTML = msg[category][0]
                    cell = row.insertCell(1)
                    cell.innerHTML = status

                    current_status = document.getElementById(msg[category][0])
                }
                else
                {
                    console.log('[SOCKETIO] WARNING: Table not found for category:', category + "_result");
                }
            }

            let status = '<div id="' + msg[category][0] + '"><div class="progress progress-info  mb-3"><div class="progress-bar " role="progressbar" style="width: 0%" aria-valuenow="0" aria-valuemin="0" aria-valuemax="100"></div></div>' + msg[category][2] 
                if(msg[category][1] < 100)
                {
                    status = '<div id="' + msg[category][0] + '"><div class="progress progress-info  mb-3"><div class="progress-bar " role="progressbar" style="width: ' + msg[category][1] + '%" aria-valuenow="' + msg[category][1] + '" aria-valuemin="0" aria-valuemax="100"></div></div>' + msg[category][2] 
                }
                else if(msg[category][1] == 100)
                {
                    status = '<div id="' + msg[category][0] + '"><i class="mdi mdi-check text-success mx-1"></i>Done</div>'  + msg[category][2] 
                }
                else if(msg[category][1] == 101)
                {
                    status = '<div id="' + msg[category][0] + '"><i class="mdi mdi-close text-danger mx-1"></i>Failed</div>' + msg[category][2] 
                }
                else if(msg[category][1] == 102)
                {
                    status = '<div id="' + msg[category][0] + '"><i class="mdi mdi-information-outline text-info mx-1"></i>Readme</div>' + msg[category][2] 
                }
                else if(msg[category][1] == 103)
                {
                    status = '<div id="' + msg[category][0] + '"><div class="spinner-border spinner-border-sm text-primary" role="status"></div> In progress</div>' + msg[category][2] 
                }
                else if(msg[category][1] == 104)
                {
                    status = '<div id="' + msg[category][0] + '"></div>' + msg[category][2] 
                }
                else if(msg[category][1] == 105)
                {
                    status = '<div id="' + msg[category][0] + '"><i class="mdi mdi-minus-circle-outline text-secondary mx-1"></i>Not needed</div>' + msg[category][2] 
                }
                else if(msg[category][1] == 106)
                {
                    status = '<div id="' + msg[category][0] + '"><i class="mdi mdi-timer-sand text-primary mx-1"></i> Pending</div>' + msg[category][2] 
                }
                else
                {
                    status = '<div id="' + msg[category][0] + '"><i class="mdi mdi-help text-primary mx-1"></i>Unknown</div>' + msg[category][2] 
                }
                if(current_status)
                    current_status.innerHTML = status
        }
        
    })

    // Delay the focus slightly to ensure rendering is complete
    const focusables = [...document.querySelectorAll('.focusable')];
    setTimeout(() => {
        const focusables = [...document.querySelectorAll('.focusable')];
        for (const el of focusables) {
            if (
                !el.disabled &&
                el.offsetParent !== null && // visible in layout
                el.tagName === "INPUT" &&
                el.type === "text"
            ) {
                el.focus();
                el.select(); // also select text to make typing more intuitive
                console.log("Focused on:", el);
                break;
            }
        }
    }, 300); // delay longer than before

    setTimeout(() => {
        console.log("Final active element:", document.activeElement);
    }, 500);
})

function settings_update_icon(elementId) {
    var input = document.getElementById(elementId);
    var div   = document.getElementById(elementId + '.div');
    if (!input || !div) return;

    var iconName = input.value.trim() || 'help'; 
    // grab the first <i> inside the div
    var iconEl   = div.getElementsByTagName('i')[0];

    if (iconEl) {
      // reset its classes to "mdi mdi-{your-input-value}"
      iconEl.className = 'mdi mdi-' + iconName;
    }
  }

function split_attribute(sourceFieldId, ...targetSuffixes) {
    try {
        // Get the source field element
        const sourceInput = document.getElementById(sourceFieldId + ".scan");
        if (!sourceInput) {
            console.warn("Source input not found:", sourceFieldId);
            return;
        }
    
        // Get the prefix for derived fields
        const prefix = sourceFieldId;

        // Find the separator from the corresponding select element
        const separatorSelectId = `${prefix}.separator`;
        const separatorSelect = document.getElementById(separatorSelectId);
        const separator = separatorSelect ? separatorSelect.value : "_"; // default "_"

        // Get value and split
        const parts = sourceInput.value.split(separator);

        // For each target, fill the corresponding input field
        for (let i = 0; i < targetSuffixes.length; i++) {
            const targetSuffix = targetSuffixes[i];
            const targetFieldId = `${prefix}.${targetSuffix}`;
            const targetField = document.getElementById(targetFieldId);

            if (targetField) {
                targetField.value = parts[i] !== undefined ? parts[i] : "";
            }
        }
    } catch (e) {
        console.error("Error in split function:", e);
    }
}