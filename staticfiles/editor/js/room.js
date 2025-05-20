require.config({ paths: { 'vs': 'https://cdn.jsdelivr.net/npm/monaco-editor/min/vs' } });


const channel_id = "{{channel.id}}";
const userprofile = "{{userprofile}}"

require(['vs/editor/editor.main'], function () {
    let editor;
    let lan;
    let value = '';
    let read_only = true;
    let flag = true
    const roomName = "{{room_name}}";

    let permitted_users = "{{channel.has_permission.all}}"
    if (permitted_users.includes("{{userprofile}}")) {
        console.log("Yes you have permission")
        read_only = false;
    } else {
        console.log('no you do no have any permission')
        read_only = true;
    }

    if ("{{channel.programing_language}}" === "PYTHON") {
        lan = 'python';
        value = `# Write your Python code here\nprint("Hello, World!")`;
    } else if ("{{channel.programing_language}}" === "C") {
        lan = 'cpp';
    } else {
        lan = 'plaintext';
    }

    console.log("Selected Languagessss: {{channel.programing_language}}");

    editor = monaco.editor.create(document.getElementById('editor'), {
        // value: value,
        language: lan,
        theme: 'vs-dark',
        automaticLayout: true,
        readOnly: read_only,
        fontFamily: " 'JetBrains Mono', serif",
        fontSize: 16, // Optional: Adjust font size
        fontLigatures: true // Enable ligatures if the font supports it
    });
    console.log("read only status: ", read_only)

    document.getElementById("theme-selector").addEventListener("change", function (e) {
        const selectedTheme = e.target.value;
        console.log('Selected Theme:', selectedTheme);
        monaco.editor.setTheme(selectedTheme);
    });

    console.log(lan)
    let debounceTimer;
    let isLocalChange = false;
    const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
    const socket = new WebSocket(`${protocol}://` + window.location.host + '/ws/ac/' + roomName + '/' + "{{userprofile.id}}");


    editor.onDidChangeModelContent((event) => {
        if (!isLocalChange) {
            const changes = event.changes.map(change => ({
                range: {
                    startLineNumber: change.range.startLineNumber,
                    startColumn: change.range.startColumn,
                    endLineNumber: change.range.endLineNumber,
                    endColumn: change.range.endColumn
                },
                text: change.text
            }));
            // if (flag) {
            socket.send(JSON.stringify({
                type: 'code_change',
                changes: changes,
                coding_by: editorElement.dataset.user,
                user_image: editorElement.dataset.user_image
            }));
            // }
            // flag = true
        }
    });


    socket.onopen = function () {
        console.log('websocket opend')
        socket.send(JSON.stringify({ type: "allconnecteduser" }));
    };
    socket.onmessage = function (e) {
        const data = JSON.parse(e.data);
        console.log('Message received from server:', data);
        console.log('upro, ', data.coding_by, userprofile)
        // const data = JSON.parse(e.data);

        if (data.coding_by !== userprofile) {
            if (data.type === 'code_change' && !isLocalChange) {
                isLocalChange = true;
                const model = editor.getModel();
                // Apply each change individually
                model.applyEdits(data.changes.map(change => ({
                    range: new monaco.Range(
                        change.range.startLineNumber,
                        change.range.startColumn,
                        change.range.endLineNumber,
                        change.range.endColumn
                    ),
                    text: change.text,
                    // Optional: Force move markers (for cursors)
                    forceMoveMarkers: true
                })));
                isLocalChange = false;
            }
        }
        if (data.coding_by) {
            const coding_by_img = document.getElementById('coding_by_img')
            coding_by_img.src = data.user_image
            coding_by_img.title = data.coding_by
            const indicate = document.getElementById('indicate')
            indicate.classList.replace('hidden', 'not_hidden')
        }

        if (data.connected_users) {
            console.log('Connected users', data.connected_users)
            const connected_users = data.connected_users
            const x = document.getElementById('joined')
            connected_users.forEach(user => {
                addConnectedUser(user.username, user.image)
                // console.log(user.username, user.image)
                x.play()
            });
            // addConnectedUser(data.user, data.userimage)
            if (userprofile === data.first_user) {

                console.log('editor value is :  ', editor.getValue())
                socket.send(JSON.stringify({
                    'type': 'sync_editor',
                    'initial_code': editor.getValue(),
                    'first_user': data.first_user
                }))
            }
        }
        if (data.type === "user_disconnected") {
            removeConnectedUser(data.left_user);
        }

        if (data.type === "initial_change") {
            const initial_code = data.initial_code

            console.log('Initial_code is: ', initial_code, data.first_user, userprofile);
            if (data.first_user !== userprofile) {
                isLocalChange = true; // Set this to true to indicate a local change
                editor.setValue(initial_code); // Set the editor value without triggering WebSocket
                isLocalChange = false; // Reset after setting the value
            }
        }
    };




    function scrollToBottom() {
        const scrollHeight = document.body.scrollHeight;

        // window.scrollTo(0, scrollHeight);
    }

    const editorElement = document.getElementById('editor');


    document.querySelectorAll('.file-button').forEach(button => {
        button.addEventListener('click', function () {
            if (!read_only) {
                const content = this.getAttribute('data-content');
                const file_id = this.dataset.file_id
                const file_name = this.dataset.file_name
                editor.setValue(content);
                editorElement.dataset.file_id = file_id
                editorElement.dataset.file_name = file_name
                console.log(editorElement.dataset.file_id);
                document.getElementById('inputs').value = ''
                document.getElementById('output').innerText = ''

            } else {
                alert("You Don't Have any permission Permisssion")
            }
        });
    });


    document.getElementById('save-code').addEventListener('click', () => {
        const inputContainer = document.getElementById('input-container');
        document.getElementById('file-name').value = editorElement.dataset.file_name;
        inputContainer.classList.toggle('hidden');
    });
    document.getElementById('submit-name').addEventListener('click', () => {
        const inputContainer = document.getElementById('file-name');
        const name = inputContainer.value;
        const code = editor.getValue();
        const file_id = editorElement.dataset.file_id;
        const channel_id = "{{channel.id}}"

        fetch('/save-code/', {
            method: "POST",
            headers: {
                headers: {
                    'Content-Type': 'application/json',
                }
            },
            body: JSON.stringify({
                "name": name,
                'code': code,
                'file_id': file_id,
                'channel_id': channel_id
            })


        })
            .then(response => response.json())
            .then(data => {
                if (data.msg) {
                    window.location.reload();
                } else if (data.error) {
                    alert(data.error)
                }
            })
    })

    document.getElementById("load_data").addEventListener('click', () => {
        console.log('Clicked')
        const savedCode = localStorage.getItem(`${channel_id}_cod`);
        if (savedCode) {
            editor.setValue(savedCode);
        }
    })


    const save_code_in_local_storage = () => {
        let value = editor.getValue();
        console.log('Done')
        if (value) {
            localStorage.setItem(`${channel_id}_cod`, value);
        }
    }

    const btn = document.getElementById('run-code');


    // const socket = new WebSocket('ws://' + window.location.host + '/ws/ac/' + roomName + '/' + "{{userprofile.id}}");




    let taskId = null



    function addConnectedUser(username, imageUrl) {
        const userList = document.getElementById('connected-users');
        if (!userList) {
            console.error('User list element not found!');
            return;
        }

        // Check if the user is already in the list
        const userExists = Array.from(userList.children).some(
            item => item.querySelector('img')?.title === username
        );
        if (userExists) {
            console.log(`User ${username} is already connected.`);
            return;
        }

        // Create the new user list item
        const listItem = document.createElement('li');
        listItem.className = 'd-flex justify-content-center align-items-center me-1';

        listItem.innerHTML = `
            <div class="align-items-center">
                <img src="${imageUrl}" alt="" style="width: 30px; height: 30px" 
                    title="${username}" class="rounded-circle" />
            </div>
        `;

        userList.appendChild(listItem);
    }

    function removeConnectedUser(username) {
        const userList = document.getElementById('connected-users');
        if (!userList) {
            console.error('User list element not found!');
            return;
        }

        // Find the user's list item by the title attribute
        const userItem = Array.from(userList.children).find(
            item => item.querySelector('img')?.title === username
        );

        // Remove the user's list item
        if (userItem) {
            userList.removeChild(userItem);
            console.log(`User ${username} has been removed.`);
        }
    }



    socket.onclose = function (e) {
        console.log('WebSocket closed unexpectedly');
    };



    // ===========================================================================================================================



    // ===========================================================================================================================
    // const task_socket = new WebSocket('ws://' + window.location.host + '/ws/task-result/' + roomName + '/');

    const task_socket = new WebSocket(`${protocol}://${window.location.host}/ws/task-result/${roomName}/`);
    task_socket.onmessage = function (event) {
        console.log(event)
        console.log("Task ouput is : ", JSON.parse(event.data))
        data = JSON.parse(event.data)
        const output_dev = document.getElementById('output')
        output_dev.textContent += data.output;
        document.getElementById('executed-by').innerText = `Executed by: ${data.code_executed_by}`;

        let img = document.getElementById('run_code_icon')
        img.src = "{% static 'icons/execute.png' %}"
        img.style.background = "none"
    }
    function startTask(code, code_executed_by, inputs, language) {
        fetch('/start-task/', {
            method: 'POST',
            headers: {
                'Content-type': 'application/json',
            },
            body: JSON.stringify({
                "code": code,
                "code_executed_by": code_executed_by,
                "inputs": inputs,
                "roomName": roomName,
                "language": language
            })
        })
            .then(response => response.json())
            .then(data => {
                const task_id = data.task_id
                console.log('Your task id is: ', task_id)
            })
            .catch(error => {
                console.error('Error starting task:', error);
            });
    }

    btn.addEventListener('click', function () {
        const code = editor.getValue();
        const code_executed_by = btn.dataset['executed'];
        const language = btn.dataset['language'];
        const inputs = document.getElementById('inputs').value
        let img = this.querySelector("img");
        const output_dev = document.getElementById('output')
        output_dev.textContent = ""

        img.src = "{% static 'icons/loading.gif' %}";
        startTask(code, code_executed_by, inputs, language);


    });


    function sendCodeForExecution(code, code_executed_by, inputs) {
        socket.send(JSON.stringify({
            'code': code,
            'code_executed_by': code_executed_by,
            'inputs': inputs
        }));
    }
    // ===========================================================================================================================




    const permission_socket = new WebSocket(`${protocol}://` + window.location.host + '/ws/permission/' + roomName + '/')


    permission_socket.onmessage = function (e) {
        const data = JSON.parse(e.data);

        console.log(data);

        const userId = data.user_id;
        const type = data.type;

        // Update the UI for all users
        const permissionButton = document.getElementById(`user_perm_${userId}`);
        const statusBadge = document.getElementById(`user_has_perm_${userId}`);

        if (userprofile === "{{channel.created_by}}") {
            if (type === "remove") {
                // Update button to "Give Permission"
                permissionButton.innerHTML = 'Give permission';
                permissionButton.dataset.type = "add";
                permissionButton.classList.remove("badge-danger");
                permissionButton.classList.add("badge-info");

                // statusBadge.classList.add("hidden");
            } else if (type === "add") {
                permissionButton.innerHTML = 'Remove permission';
                permissionButton.dataset.type = "remove";
                permissionButton.classList.remove("badge-info");
                permissionButton.classList.add("badge-danger");

                // statusBadge.classList.remove("hidden");
                // statusBadge.innerHTML = '<span class="text-success">Has permission</span>';
            }
        }

        if (data.user === "{{userprofile}}") {
            if (type === "remove") {
                editor.updateOptions({ readOnly: true });
                statusBadge.innerHTML = '<span class="text-danger">No permission</span>';
            } else if (type === "add") {
                editor.updateOptions({ readOnly: false });
                statusBadge.innerHTML = '<span class="text-success">Has permission</span>';
            }
        }
        if (type === "remove") {
            statusBadge.innerText = 'no permission';
            statusBadge.className = ''
            statusBadge.classList.add("badge", "rounded-pill", "badge-danger")
        } else if (type === "add") {
            statusBadge.innerText = 'has permission';
            statusBadge.className = ''
            statusBadge.classList.add("badge", "rounded-pill", "badge-info")
        }
    }

    document.querySelectorAll(".permission").forEach(button => {
        button.addEventListener("click", function () {
            const username = this.getAttribute("data-user_name");
            const user_id = this.getAttribute("data-user_id");
            const channelId = this.getAttribute("data-channel_id");
            const type = this.getAttribute('data-type')

            permission_socket.send(JSON.stringify({
                'user_name': username,
                'user_id': user_id,
                'type': type
            }))

        });
    });


});