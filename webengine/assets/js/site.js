function setting_add_list(name)
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

     settings_list_format(name)
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

     //Add the line
     var div = document.getElementById(name + ".div")
     document.getElementById(name + ".list" + (max_nb - 1).toString()).remove();
 
     //And repush the user data
     for (var i = 0; i < max_nb - 1; i++)
     {
         document.getElementById(name + ".list" + (i).toString()).value = content_name[i];
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


$(document).ready(function() {    
    var socket = io.connect('http://' + document.domain + ':' + location.port);
    setTimeout(test_connect, 1000)
    function test_connect(){socket.emit("user_connected") }

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
        let div = document.getElementById(msg["id"])
        if(div)
            div.innerHTML = msg["content"]
    })

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
        for(let level of Object.keys(msg))
        {
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
                div.outerHTML = '<button class="mx-1 btn btn-' + msg[id][2] + '" id="' + id + '"><h2><i class="mdi mdi-' + msg[id][0] + ' text-light mx-1"></i></h2>' + msg[id][1] + '</button>'
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
        for(let category of Object.keys(msg))
        {
            //Do we already have the status in the table
            let current_status = document.getElementById(msg[category][0])
            if(!current_status)
            {
                let table = document.getElementById(category + "_result")
                console.log(category)
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
                    status = '<div id="' + msg[category][0] + '"><i class="mdi mdi-alert text-warning mx-1"></i>Readme</div>' + msg[category][2] 
                }
                else if(msg[category][1] == 103)
                {
                    status = '<div id="' + msg[category][0] + '"><div class="spinner-border spinner-border-sm text-primary" role="status"></div> In progress</div>' + msg[category][2] 
                }
                else
                {
                    status = '<div id="' + msg[category][0] + '"><i class="mdi mdi-help text-primary mx-1"></i>Unknown</div>' + msg[category][2] 
                }
                if(current_status)
                    current_status.innerHTML = status
        }
        
    })
})

function path_init()
{
    console.log("Path init")
    //Search the path results items
    var paths = document.getElementsByClassName('path_result');
    for (var i = 0; i < paths.length; ++i) 
    {
        var item = paths[i]; 
        var div = document.getElementById(item.id + "_div");
        if(!document.getElementById(item.id.replace("Path", "Found")))
        {
            div.innerHTML += "<input type=\"hidden\" name=\"" + item.id.replace("Path", "Found") + "\" id=\"" + item.id.replace("Path", "Found") + "\" value=" + false + ">";
        }
    }

    for (var i = 0; i < paths.length; ++i) 
    {
        // Recover the path results that will need to be filled
        var item = paths[i];  
        //var is_symbol = true

        // Fill the level 0 items
        var level0 = document.getElementById(item.id + "_level0")
        var symbol_source;
        console.log(level0.getAttribute("source"))
        //if(level0.getAttribute("source") == "1") 
        //{
        //    symbol_source = symbols;
        //    is_symbol = true;
        //}
        //else
        //{
        //    symbol_source = footprints;
        //    is_symbol = false
        //}
        //console.log(is_symbol)
        var path_variable = level0.getAttribute("source")
        symbol_source = window[path_variable]
        console.log(symbol_source)
        
        for (sym in symbol_source)
        {   
            var newOption = document.createElement('option');
            newOption.value = sym
            newOption.textContent = sym
            level0.appendChild(newOption)
        }
        var result_splitted  = item.value.split("/");
        var lib_ref = document.getElementById(item.id.replace("Path", "Ref")).value;
        document.getElementById(item.id.replace("Path", "Ref")).remove();


        // Set the level 0 item
        if(item.value)
        {
            level0.value = result_splitted[1];
            for (j = 1; j < result_splitted.length; j++)
            {
                path_add_level(item.id, path_variable, j-1);
                if(document.getElementById(item.id + "_level" + (j).toString()))
                    document.getElementById(item.id + "_level" + (j).toString()).value = result_splitted[j+1];
            }
        }

        // Set the library path
        if(document.getElementById(item.id.replace("Path", "Ref")))
        {
            document.getElementById(item.id.replace("Path", "Ref")).value = lib_ref;
            path_check(item.id, path_variable)
        }
    }
}

function path_check(id, path_variable)
{
    var current_cpnt_list = window[path_variable]
    console.log(id)
    // See if the symbols and footprint are correct
    if (document.getElementById(id.replace("Path", "Ref")))
    {
        path = document.getElementById(id).value;
        path = path.split('/')
        var Found = true;
        for (i = 1; i <= path.length; i++)
        {
            if (path[i] in current_cpnt_list)
            {
                current_cpnt_list = current_cpnt_list[path[i]]
            }
            else
            {
                Found = false
            }
        }
        if (Found && document.getElementById(id.replace("Path", "Ref")))
        {
            if (current_cpnt_list.includes(document.getElementById(id.replace("Path", "Ref")).value))
            {
                document.getElementById(id.replace("Path", "Found")).value = true;
            }
        }
    }
}

function path_add_level(id, path_variable, current_level)
{
    console.log("In path level:")
    console.log(path_variable)
    console.log(current_level)
    var current_symbol = window[path_variable]
    console.log(current_symbol)

    var current_selection = document.getElementById(id + "_level" + (current_level).toString());
    if (current_selection)
    {
        current_selection = current_selection.value

        // Start by recovering all the selected values up to now
        var selected = []
        for (i = 0; i <= current_level; i++)
        {
            selected.push(document.getElementById(id + "_level" + (i).toString()).value)
            current_symbol = current_symbol[selected[i]]
        }

        // Clear all the level that come after this one
        for (i = current_level + 1; i < 100; i++)
        {
            var level = document.getElementById(id + "_level" + (i).toString())
            if (level)
            {
                //Clear the information
                for(j = level.options.length - 1; j > 0; j--) 
                {
                    level.remove(j);
                }
            }
            else
            {
                i = 100
            }
        }
        //Also clear the final item
        var level = document.getElementById(id.replace("Path", "Ref"))
        if (level)
        {
            //Clear the information
            for(j = level.options.length - 1; j > 0; j--) 
            {
                level.remove(j);
            }
        }

        //We have an other folder
        if (current_selection.toLowerCase().includes("lib"))
        {
            // Add the select form if necessary
            if(document.getElementById(id.replace("Path", "Ref")) === null)
            {
                var div = document.getElementById(id + "_div");
                console.log("setting final to ")
                console.log(path_variable)
                div.innerHTML += "<select class=\"form-control\" id=\"" + id.replace("Path", "Ref") + "\" name=\"" + id.replace("Path", "Ref") + "\" class=\"path\" onchange=\"path_check('" + id + "', '" + path_variable + "')\"><option>Veillez sélectionner</option></select>";
            }

            // Fill the new level
            var level = document.getElementById(id.replace("Path", "Ref"));

            // Recover the json object of the current level
            for (i = 0; i < current_symbol.length; i++)
            {
                var newOption = document.createElement('option');
                newOption.value = current_symbol[i];
                newOption.textContent = current_symbol[i];
                level.appendChild(newOption);
            }
        }
        else
        {
            // Add the select form if necessary
            if(document.getElementById(id + "_level" + (current_level + 1).toString()) === null)
            {
                var div = document.getElementById(id + "_div");
                console.log("setting path to ")
                console.log(path_variable)
                div.innerHTML += "<select class=\"form-control\" id=\"" + id + "_level" + (current_level + 1).toString() + "\" class=\"path\" onchange=\"path_add_level('" + id + "', '" + path_variable + "', " + (current_level + 1).toString() + ")\"><option>Veillez sélectionner</option></select>";
            }

            // FIll the new level
            var level = document.getElementById(id + "_level"  + (current_level + 1).toString())

            // Recover the json object of the current level
            for (sym in current_symbol)
            {
                var newOption = document.createElement('option');
                newOption.value = sym;
                newOption.textContent = sym;
                level.appendChild(newOption);
            }
        }

        //Reset all the selected values and update the width
        col_width = 12/(current_level + 2)
        for (i = 0; i <= current_level; i++)
        {
            document.getElementById(id + "_level" + (i).toString()).value = selected[i];
            // console.log(id + "_level" + (i).toString())
            // console.log(col_width)
            // document.getElementById(id + "_level" + (i).toString()).removeAttribute("class");
            // document.getElementById(id + "_level" + (i).toString()).classList.add("form-control");
            // document.getElementById(id + "_level" + (i).toString()).classList.add("col-md-" + (col_width).toString());
        }

        //Updated the path variable that will be transmited
        var current_path = ""
        for(var i = 0; i <= current_level; i++)
        {
            current_path += "/" + document.getElementById(id + "_level" + (i).toString()).value;
        }

        document.getElementById(id).value = current_path;

        // if (is_symbol)
        // {
        //     console.log("Is symbol")
        //     document.getElementById(id).value = "Symbols" + current_path;
        // }
        // else
        // {
        //     console.log("Is footprint")
        //     document.getElementById(id).value = "Footprints" + current_path;
        // }
    }
}

function path_extend(base_name, base_item, group_to_extend)
{
    // Start by recovering the information from the user
    var user_info = []
    for (var i = 0; i < 100; i ++)
    {
        var current_select = document.getElementById(base_name + ".Group" + (group_to_extend).toString() + "." + base_item + "_level" + (i).toString());
        if(current_select)
        {
            user_info.push(current_select.value);
        }
        else
        {
            break;
        }
    }

    // Look for the last level:
    current_select = document.getElementById(base_name + ".Group" + (group_to_extend).toString() + "." + base_item.replace("Path", "Ref"));
    if(current_select)
    {
        user_info.push(current_select.value)
    }

    //Then apply to all other targets
    console.log(user_info)
    for (var i = 0; i < 100; i ++)
    {
        if(i != group_to_extend)
        {
            for(j = 0; j < user_info.length; j++)
            {
                var current_select = document.getElementById(base_name + ".Group" + (i).toString() + "." + base_item + "_level" + (j).toString());
                console.log(base_name + ".Group" + (i).toString() + "." + base_item + "_level" + (j).toString())
                if(current_select)
                {
                    current_select.value = user_info[j]
                }
                else
                {  
                    // Are we done with all the groups (in which case j == 0), or is it that the select level is not implemented?
                    if(j > 0)
                    {
                        //For now: always footprint
                        path_add_level(base_name + ".Group" + (i).toString() + "." + base_item, false, j-1);
                        current_select = document.getElementById(base_name + ".Group" + (i).toString() + "." + base_item + "_level" + (j).toString());
                        if(current_select)
                        {
                            current_select.value = user_info[j]   
                        }
                        else
                        {
                            // Last level?
                            current_select = document.getElementById(base_name + ".Group" + (i).toString() + "." + base_item.replace("Path", "Ref"));
                            console.log(base_name + ".Group" + (i).toString() + "." + base_item.replace("Path", "Ref"))
                            if(current_select)
                            {
                                current_select.value = user_info[j] 
                            }
                        }
                    }
                    else
                    {
                        i = 100;
                    }
                }
            }
        }
    }
}

document.addEventListener("DOMContentLoaded", function() {
    path_init();
  });