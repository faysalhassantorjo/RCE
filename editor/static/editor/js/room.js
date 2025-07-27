// room.js

// ===== GLOBAL VARIABLES =====
let editor;
let lan;
let value = '';
let read_only = true;
let flag = true;
let debounceTimer;
let isLocalChange = false;
let currentDecorations = [];
let taskId = null;

// User tracking variables
let userPositions = new Map();
let userDecorations = new Map();
let cursorDecorations = new Map();
let lineDecorations = new Map();

// WebSocket connections
let socket;
let code_paste;
let task_socket;
let permission_socket;

// ===== DOM ELEMENTS =====
let editorElement;
let notification;
let pasteList;

// ===== CONFIGURATION =====
let protocol;
let channel_id;
let userprofile;
let userprofile_id;
let roomName;
let permitted_users;
let selected_programing_language;
let channel_created_by;

// ===== INITIALIZATION FUNCTION =====
function initializeConfiguration() {
    console.log('Initializing configuration...');
    console.log('Document ready state:', document.readyState);
    console.log('Body element:', document.body);
    console.log('Body dataset:', document.body.dataset);
    
    // Initialize DOM elements
    editorElement = document.getElementById('editor');
    notification = document.getElementById("notification");
    pasteList = document.getElementById("pasteList");

    console.log('DOM elements found:', {
        editor: !!editorElement,
        notification: !!notification,
        pasteList: !!pasteList
    });

    // Initialize configuration from data attributes
    protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
    channel_id = document.body.dataset.channelId;
    userprofile = document.body.dataset.user;
    userprofile_id = document.body.dataset.userId;
    roomName = document.body.dataset.roomName;
    permitted_users = document.body.dataset.permittedUsers;
    selected_programing_language = document.body.dataset.language;
    channel_created_by = document.body.dataset.channelCreatedBy;

    console.log('Configuration values:', {
        channel_id,
        userprofile,
        userprofile_id,
        roomName,
        permitted_users,
        selected_programing_language,
        channel_created_by
    });

    // Validate that we have the required data
    if (!channel_id || !userprofile || !userprofile_id || !roomName) {
        console.error('Missing required configuration data');
        return false;
    }

    console.log('Configuration initialized successfully');
    return true;
}

// ===== UTILITY FUNCTIONS =====
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

function copy_output() {
    const copyText = document.getElementById('output').innerText;
    navigator.clipboard.writeText(copyText)
        .then(() => {
            alert("Copied the text: " + copyText);
        }).catch(err => {
            console.error('Failed to copy text: ', err);
        });
}

function hide_container() {
    document.getElementById('input-container').classList.add('hidden');
}

// ===== MODAL FUNCTIONS =====
function initializeModal() {
    const modal = document.getElementById('testModal');
    const showModalBtn = document.getElementById('showModalBtn');
    const cancelBtn = document.getElementById('cancelBtn');

    if (showModalBtn) {
        showModalBtn.addEventListener('click', function () {
            modal.classList.remove('d-none');
            modal.style.opacity = '0';
            setTimeout(() => {
                modal.style.transition = 'opacity 0.3s ease';
                modal.style.opacity = '1';
            }, 10);
        });
    }

    if (cancelBtn) {
        cancelBtn.addEventListener('click', hideModal);
    }
}

function hideModal() {
    const modal = document.getElementById('testModal');
    modal.style.transition = 'opacity 0.3s ease';
    modal.style.opacity = '0';
    setTimeout(() => {
        modal.classList.add('d-none');
        modal.style.transition = '';
        modal.style.opacity = '';
    }, 300);
}

// ===== CONTAINER MANAGEMENT =====
function startContainer(button) {
    const userId = button.dataset.user_id;
    const container_button = document.getElementById('start_container');
    
    fetch('/start-container/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            "user_id": userId
        })
    })
    .then(response => response.json())
    .then(data => {
        console.log('response: ', data);
        const status = data['container_status'];
        container_button.innerHTML = status;
        container_button.style.display = "none";
        document.getElementById('container_status').classList.remove('hidden');
    })
    .catch(error => {
        console.error('Error starting container:', error);
    });
}

// ===== SOCKET STATUS MANAGEMENT =====
function updateSocketStatus(status, message = '') {
    const statusElement = document.getElementById('socket-status-text');
    const iconElement = statusElement.querySelector('i');
    
    statusElement.classList.remove('connected', 'connecting', 'disconnected', 'error');
    
    switch(status) {
        case 'connected':
            statusElement.classList.add('connected');
            statusElement.innerHTML = `<i class="fa-solid fa-check-circle"></i> Connected`;
            setTimeout(() => {
                statusElement.style.display = 'none';
            }, 3000);
            break;
        case 'connecting':
            statusElement.classList.add('connecting');
            statusElement.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Connecting...`;
            break;
        case 'disconnected':
            statusElement.classList.add('disconnected');
            statusElement.innerHTML = `<i class="fa-solid fa-times-circle"></i> Disconnected`;
            break;
        case 'error':
            statusElement.classList.add('error');
            statusElement.innerHTML = `<i class="fa-solid fa-exclamation-triangle"></i> ${message || 'Connection Error'}`;
            break;
    }
}

// ===== USER POSITION MANAGEMENT =====
function updateUserPosition(username, userImage, position, isTyping = false) {
    if (!position) return;
    
    const { lineNumber, column } = position;
    userPositions.set(username, { position, userImage, isTyping });
    
    // Remove old decorations for this user
    if (userDecorations.has(username)) {
        editor.deltaDecorations(userDecorations.get(username), []);
        userDecorations.delete(username);
    }
    if (cursorDecorations.has(username)) {
        editor.deltaDecorations(cursorDecorations.get(username), []);
        cursorDecorations.delete(username);
    }
    if (lineDecorations.has(username)) {
        editor.deltaDecorations(lineDecorations.get(username), []);
        lineDecorations.delete(username);
    }
    
    // Add new decorations
    const decorations = [];
    
    // Line indicator (user avatar on the left)
    const lineIndicator = {
        range: new monaco.Range(lineNumber, 1, lineNumber, 1),
        options: {
            glyphMarginClassName: 'user-line-indicator',
            glyphMarginHoverMessage: { value: `${username} is coding here` },
            stickiness: monaco.editor.TrackedRangeStickiness.NeverGrowsWhenTypingAtEdges
        }
    };
    decorations.push(lineIndicator);
    
    // Cursor indicator
    const cursorIndicator = {
        range: new monaco.Range(lineNumber, column, lineNumber, column + 1),
        options: {
            className: 'user-cursor',
            hoverMessage: { value: `${username}'s cursor` },
            stickiness: monaco.editor.TrackedRangeStickiness.NeverGrowsWhenTypingAtEdges
        }
    };
    decorations.push(cursorIndicator);
    
    // Line background highlight if typing
    if (isTyping) {
        const lineHighlight = {
            range: new monaco.Range(lineNumber, 1, lineNumber, 1),
            options: {
                className: 'active-user-indicator',
                stickiness: monaco.editor.TrackedRangeStickiness.NeverGrowsWhenTypingAtEdges
            }
        };
        decorations.push(lineHighlight);
    }
    
    // Apply decorations
    const decorationIds = editor.deltaDecorations([], decorations);
    userDecorations.set(username, decorationIds);
    
    // Store individual decoration IDs for later removal
    cursorDecorations.set(username, [decorationIds[1]]);
    lineDecorations.set(username, [decorationIds[0]]);
    
    // Add CSS for user avatar
    const styleId = `user-avatar-${username}`;
    if (!document.getElementById(styleId)) {
        const style = document.createElement('style');
        style.id = styleId;
        style.textContent = `
            .user-line-indicator[data-user="${username}"] {
                background-image: url('${userImage}');
            }
        `;
        document.head.appendChild(style);
    }
    
    updateConnectedUsersDisplay();
}

function removeUserPosition(username) {
    userPositions.delete(username);
    
    if (userDecorations.has(username)) {
        editor.deltaDecorations(userDecorations.get(username), []);
        userDecorations.delete(username);
    }
    if (cursorDecorations.has(username)) {
        editor.deltaDecorations(cursorDecorations.get(username), []);
        cursorDecorations.delete(username);
    }
    if (lineDecorations.has(username)) {
        editor.deltaDecorations(lineDecorations.get(username), []);
        lineDecorations.delete(username);
    }
    
    updateConnectedUsersDisplay();
}

// ===== CONNECTED USERS MANAGEMENT =====
function updateUserCount() {
    const userList = document.getElementById('connected-users');
    const countSpan = document.getElementById('user-count');
    if (userList && countSpan) {
        countSpan.textContent = userList.children.length;
    }
}

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
    listItem.innerHTML = `
        <div class="user-card">
            <div class="user-avatar">
                <img src="${imageUrl}" alt="${username}" title="${username}">
            </div>
            <span class="user-name">${username}</span>
        </div>
    `;

    userList.appendChild(listItem);
    updateUserCount();
    updateConnectedUsersDisplay();
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
        updateUserCount();
    }
    
    // Also remove from user positions tracking
    removeUserPosition(username);
}

function updateConnectedUsersDisplay() {
    const userList = document.getElementById('connected-users');
    if (!userList) return;
    
    // Update existing user cards with coding information
    Array.from(userList.children).forEach(userItem => {
        const img = userItem.querySelector('img');
        const username = img?.title;
        
        if (username && userPositions.has(username)) {
            const userData = userPositions.get(username);
            const { position, isTyping } = userData;
            const { lineNumber, column } = position;
            
            // Update the user card to show coding status
            const userCard = userItem.querySelector('.user-card');
            if (userCard) {
                userCard.style.borderLeft = `3px solid ${isTyping ? '#4ecdd1' : '#666'}`;
                userCard.style.backgroundColor = isTyping ? 'var(--sidebar-bg)' : 'var(--sidebar-bg)';
                
                // Add or update coding status info
                let statusInfo = userCard.querySelector('.coding-status');
                if (!statusInfo) {
                    statusInfo = document.createElement('div');
                    statusInfo.className = 'coding-status';
                    statusInfo.style.cssText = `
                        font-size: 10px;
                        color: #858585;
                        margin-top: 4px;
                    `;
                    userCard.appendChild(statusInfo);
                }
                
                statusInfo.innerHTML = `
                    Line ${lineNumber}, Col ${column}
                    ${isTyping ? '<span class="text-success ms-1">• typing</span>' : ''}
                `;
            }
        } else if (username) {
            // Remove coding status if user is not coding
            const userCard = userItem.querySelector('.user-card');
            if (userCard) {
                userCard.style.borderLeft = 'none';
                const statusInfo = userCard.querySelector('.coding-status');
                if (statusInfo) {
                    statusInfo.remove();
                }
            }
        }
    });
}

// ===== FILE MANAGEMENT =====
function initializeFileManagement() {
    // File button click handlers
    document.querySelector('.file-list').addEventListener('click', function (e) {
        const button = e.target.closest('.file-button');
        if (button) {
            if (!read_only) {
                const content = button.getAttribute('data-content');
                const file_id = button.dataset.file_id;
                const file_name = button.dataset.file_name;
                editor.setValue(content);
                editorElement.dataset.file_id = file_id;
                editorElement.dataset.file_name = file_name;
                console.log(editorElement.dataset.file_id);
                document.getElementById('output').innerText = '';

                // Handle active class
                document.querySelectorAll('.file-button').forEach(btn => btn.classList.remove('active'));
                button.classList.add('active');
            } else {
                alert("You Don't Have any Permission");
            }
        }
    });

    // New file button
    document.getElementById('new-file-btn').addEventListener('click', () => {
        document.querySelector('.create-file-section').classList.toggle('hidden');
    });

    // File creation confirmation
    document.getElementById('file-create-confirm').addEventListener('click', (e) => {
        e.preventDefault();

        const file_name = document.forms['file_creation']['name'].value;

        fetch('/create-file/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                file_name: file_name,
                channel_id: channel_id,
                user_id: userprofile_id
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                notification.innerText = "File Created Successfully";
                notification.style.display = 'block';
                setTimeout(() => {
                    notification.style.display = "none";
                }, 2000);

                const fileList = document.querySelector('.file-list');
                const li = document.createElement('li');
                li.classList.add('file-item');

                li.innerHTML = `
                    <button class="file-button w-100 text-start d-block" data-content="" data-file_id="${data.id}" data-file_name="${file_name}">
                        <div class="d-flex justify-content-between align-items-center">
                            <div class="d-flex align-items-center">
                                <i class="fa-solid fa-file file-icon me-2"></i>
                                <span class="file-name">${file_name}</span>
                                &nbsp;
                                <img src="${data.user_image}" height="25" width="25" alt="User" class="rounded-circle">
                            </div>
                        </div>
                    </button>
                `;

                fileList.prepend(li);
                document.querySelector('.create-file-section').classList.toggle('hidden');
            } else if (data.error) {
                notification.innerText = "Something went wrong";
                notification.style.display = 'block';
            }
        });
    });
}

// ===== CODE EXECUTION =====
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
        const task_id = data.task_id;
        console.log('Your task id is: ', task_id);
    })
    .catch(error => {
        console.error('Error starting task:', error);
    });
}

// ===== PASTE HISTORY =====
function initializePasteHistory() {
    const toggleButton = document.getElementById("toggleButton");
    const pasteHistory = document.getElementById("pasteHistory");

    toggleButton.addEventListener("click", () => {
        const isVisible = pasteHistory.style.display === "block";
        pasteHistory.style.display = isVisible ? "none" : "block";
    });
}

// ===== MEMBERS PANEL =====
function initializeMembersPanel() {
    const membersPanel = document.querySelector('.members');
    const toggleBtn = document.querySelector('#toggleMembers');
    const closeBtn = document.querySelector('#closeMembers');

    toggleBtn.addEventListener('click', () => {
        membersPanel.classList.add('visible');
    });

    closeBtn.addEventListener('click', () => {
        membersPanel.classList.remove('visible');
    });
}

// ===== WEB SOCKET CONNECTIONS =====
function initializeWebSockets() {
    // Main collaboration socket
    socket = new WebSocket(`${protocol}://${window.location.host}/ws/ac/${roomName}/${userprofile_id}`);
    
    socket.onopen = function () {
        console.log('websocket opened');
        updateSocketStatus('connected');
        if (socket.readyState === WebSocket.OPEN) {
            socket.send(JSON.stringify({ type: "allconnecteduser" }));
            
            // Send current position
            const position = editor.getPosition();
            socket.send(JSON.stringify({
                type: 'cursor_position',
                cursor_position: position,
                coding_by: editorElement.dataset.user,
                user_image: editorElement.dataset.user_image
            }));
        }
    };

    socket.onmessage = function (e) {
        const data = JSON.parse(e.data);

        if (data.coding_by !== userprofile) {
            // Handle cursor position updates
            if (data.type === 'cursor_position' && userprofile !== data.coding_by) {
                updateUserPosition(data.coding_by, data.user_image, data.cursor_position, false);
            }
            
            // Handle code changes
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
                    forceMoveMarkers: true
                })));

                const cursorPosition = data.cursor_position;
                if (cursorPosition && userprofile !== data.coding_by) {
                    editor.setPosition(cursorPosition);
                    // Update user position as typing
                    updateUserPosition(data.coding_by, data.user_image, cursorPosition, data.is_typing || false);
                }

                isLocalChange = false;
            }
        }

        if (data.coding_by) {
            const coding_by_img = document.getElementById('coding_by_img');
            coding_by_img.src = data.user_image;
            coding_by_img.title = data.coding_by;
            const indicate = document.getElementById('indicate');
            indicate.classList.replace('hidden', 'not_hidden');
        }

        if (data.connected_users) {
            console.log('Connected users', data.connected_users);
            const connected_users = data.connected_users;
            const x = document.getElementById('joined');
            connected_users.forEach(user => {
                addConnectedUser(user.username, user.image);
                x.play();
                
                // Initialize user position if they're not the current user
                if (user.username !== userprofile) {
                    // Set initial position at line 1, column 1
                    updateUserPosition(user.username, user.image, { lineNumber: 1, column: 1 }, false);
                }
            });
            if (userprofile === data.first_user) {
                console.log('editor value is :  ', editor.getValue());
                socket.send(JSON.stringify({
                    'type': 'sync_editor',
                    'initial_code': editor.getValue(),
                    'first_user': data.first_user
                }));
            }
        }

        if (data.type === "user_disconnected") {
            removeConnectedUser(data.left_user);
            // Remove user position indicators
            removeUserPosition(data.left_user);
        }

        if (data.type === "initial_change") {
            const initial_code = data.initial_code;
            console.log('Initial_code is: ', initial_code, data.first_user, userprofile);
            if (data.first_user !== userprofile) {
                isLocalChange = true;
                editor.setValue(initial_code);
                isLocalChange = false;
            }
        }
    };

    socket.onclose = function (e) {
        console.log('WebSocket closed unexpectedly');
        updateSocketStatus('disconnected');
    };

    socket.onerror = function (error) {
        console.error('WebSocket error:', error);
        updateSocketStatus('error', 'Connection failed');
    };

    // Code paste socket
    code_paste = new WebSocket(`${protocol}://${window.location.host}/ws/code-paste/${roomName}/${userprofile}/`);
    
    code_paste.onmessage = function (event) {
        const data = JSON.parse(event.data);

        currentDecorations = editor.deltaDecorations(currentDecorations, []);

        if (data.range) {
            const range = new monaco.Range(
                data.range.startLine,
                data.range.startCol,
                data.range.endLine,
                data.range.endCol
            );

            currentDecorations = editor.deltaDecorations([], [
                {
                    range: range,
                    options: {
                        className: 'paste-highlight',
                        isWholeLine: false,
                        stickiness: monaco.editor.TrackedRangeStickiness.NeverGrowsWhenTypingAtEdges
                    }
                }
            ]);

            setTimeout(() => {
                currentDecorations = editor.deltaDecorations(currentDecorations, []);
            }, 3000);
        }

        notification.style.display = "block";
        setTimeout(() => {
            notification.style.display = "none";
        }, 2000);

        if (data.content) {
            const rangeInfo = data.range ?
                `Pasted at: L${data.range.startLine}:${data.range.startCol}` +
                (data.range.endLine !== data.range.startLine ?
                    ` → L${data.range.endLine}:${data.range.endCol}` :
                    `:${data.range.endCol}`)
                : "";

            // Add line numbers to the code
            const codeWithLineNumbers = data.content
                .split('\n')
                .map((line, i) => {
                    const lineNum = data.range ? data.range.startLine + i : i + 1;
                    return `<span class="line-number">${lineNum}</span> ${escapeHtml(line)}`;
                })
                .join('\n');

            const listItem = document.createElement("li");
            listItem.className = "list-group-item";
            listItem.innerHTML = `
                <div class="d-flex justify-content-between align-items-center mb-2">
                    <strong class='text-secondary'>${data.user}</strong>
                    <small class="text-secondary">${new Date(data.timestamp).toLocaleString()}</small>
                </div>
                ${rangeInfo ? `<div class="text-danger small mb-2">${rangeInfo}</div>` : ""}
                <pre class="bg-light p-2 rounded" style="white-space: pre; overflow-x: auto; font-family: 'JetBrains Mono', monospace; font-size: 14px; position: relative;">
                    <code style="display: block; padding-left: 2.5em;">${codeWithLineNumbers}</code>
                </pre>
            `;

            pasteList.prepend(listItem);
        }
    };

    code_paste.onclose = function () {
        console.log('Code paste WebSocket connection closed');
    };

    code_paste.onerror = function (error) {
        console.error('Code paste WebSocket error:', error);
    };

    // Task result socket
    task_socket = new WebSocket(`${protocol}://${window.location.host}/ws/task-result/${roomName}/`);
    
    task_socket.onopen = function () {
        console.log('Task socket connected');
    };
    
    task_socket.onclose = function () {
        console.log('Task socket closed');
    };
    
    task_socket.onerror = function (error) {
        console.error('Task socket error:', error);
    };
    
    task_socket.onmessage = function (event) {
        console.log(event);
        console.log("Task output is : ", JSON.parse(event.data));
        const data = JSON.parse(event.data);
        const output_dev = document.getElementById('output');
        output_dev.textContent += data.output;
        document.getElementById('executed-by').innerText = `Executed by: ${data.code_executed_by}`;

        let img = document.getElementById('run_code_icon');
        if (img) {
            img.src = "/static/icons/execute.png";
            img.style.background = "none";
        }
    };

    // Permission socket
    permission_socket = new WebSocket(`${protocol}://${window.location.host}/ws/permission/${roomName}/`);
    
    permission_socket.onopen = function () {
        console.log('Permission socket connected');
    };
    
    permission_socket.onclose = function () {
        console.log('Permission socket closed');
    };
    
    permission_socket.onerror = function (error) {
        console.error('Permission socket error:', error);
    };

    permission_socket.onmessage = function (e) {
        const data = JSON.parse(e.data);
        console.log(data);

        const userId = data.user_id;
        const type = data.type;

        // Update the UI for all users
        const permissionButton = document.getElementById(`user_perm_${userId}`);
        const statusBadge = document.getElementById(`user_has_perm_${userId}`);

        if (userprofile === channel_created_by) {
            if (type === "remove") {
                // Update button to "Give Permission"
                permissionButton.innerHTML = 'Give permission';
                permissionButton.dataset.type = "add";
                permissionButton.classList.remove("badge-danger");
                permissionButton.classList.add("badge-info");
            } else if (type === "add") {
                permissionButton.innerHTML = 'Remove permission';
                permissionButton.dataset.type = "remove";
                permissionButton.classList.remove("badge-info");
                permissionButton.classList.add("badge-danger");
            }
        }

        if (data.user === userprofile) {
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
            statusBadge.className = '';
            statusBadge.classList.add("badge", "rounded-pill", "badge-danger");
        } else if (type === "add") {
            statusBadge.innerText = 'has permission';
            statusBadge.className = '';
            statusBadge.classList.add("badge", "rounded-pill", "badge-info");
        }
    };

    // Permission button handlers
    document.querySelectorAll(".permission").forEach(button => {
        button.addEventListener("click", function () {
            const username = this.getAttribute("data-user_name");
            const user_id = this.getAttribute("data-user_id");
            const channelId = this.getAttribute("data-channel_id");
            const type = this.getAttribute('data-type');

            permission_socket.send(JSON.stringify({
                'user_name': username,
                'user_id': user_id,
                'type': type
            }));
        });
    });
}

// ===== EDITOR INITIALIZATION =====
function initializeEditor() {
    // Check permissions
    if (permitted_users.includes(userprofile)) {
        console.log("Yes you have permission");
        read_only = false;
    } else {
        console.log('no you do no have any permission');
        read_only = true;
    }

    // Set language
    if (selected_programing_language === "PYTHON") {
        lan = 'python';
        value = `# Write your Python code here\nprint("Hello, World!")`;
    } else if (selected_programing_language === "C") {
        lan = 'cpp';
    } else {
        lan = 'plaintext';
    }

    // Create editor
    editor = monaco.editor.create(document.getElementById('editor'), {
        language: lan,
        theme: 'vs-dark',
        automaticLayout: true,
        readOnly: read_only,
        fontFamily: "'JetBrains Mono', serif",
        fontSize: 14,
        fontLigatures: true,
        lineNumbers: 'on',
        glyphMargin: true,
        folding: true,
        lineDecorationsWidth: 50
    });

    // Editor event handlers
    editor.onDidPaste((event) => {
        const range = event.range;
        const pastedContent = editor.getModel()?.getValueInRange(range) || "Unable to get pasted content";

        if (code_paste.readyState === WebSocket.OPEN) {
            code_paste.send(JSON.stringify({
                type: 'paste_event',
                user: userprofile,
                room: roomName,
                content: pastedContent,
                range: {
                    startLine: range.startLineNumber,
                    startCol: range.startColumn,
                    endLine: range.endLineNumber,
                    endCol: range.endColumn,
                },
                timestamp: new Date().toISOString()
            }));
        }
    });

    // Track cursor position changes
    editor.onDidChangeCursorPosition((event) => {
        if (!isLocalChange) {
            const position = editor.getPosition();
            console.log('editorElement.dataset.user', editorElement.dataset.user, 'userprofile', editorElement.dataset.user_image);
            socket.send(JSON.stringify({
                type: 'cursor_position',
                cursor_position: position,
                coding_by: editorElement.dataset.user,
                user_image: editorElement.dataset.user_image
            }));
        }
    });
    
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
            
            const position = editor.getPosition();
            socket.send(JSON.stringify({
                type: 'code_change',
                changes: changes,
                coding_by: editorElement.dataset.user,
                user_image: editorElement.dataset.user_image,
                cursor_position: position,
                is_typing: true
            }));
            
            // Update local user position as typing
            updateUserPosition(editorElement.dataset.user, editorElement.dataset.user_image, position, true);
            
            // Clear typing indicator after a delay
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(() => {
                updateUserPosition(editorElement.dataset.user, editorElement.dataset.user_image, position, false);
            }, 2000);
        }
    });

    // Theme selector
    document.getElementById("theme-selector").addEventListener("change", function (e) {
        const selectedTheme = e.target.value;
        console.log('Selected Theme:', selectedTheme);
        monaco.editor.setTheme(selectedTheme);
    });

    // Save code button
    document.getElementById('save-code').addEventListener('click', () => {
        const inputContainer = document.getElementById('input-container');
        document.getElementById('file-name').value = editorElement.dataset.file_name;
        inputContainer.classList.toggle('hidden');
    });

    // Submit name button
    document.getElementById('submit-name').addEventListener('click', () => {
        const inputContainer = document.getElementById('file-name');
        const name = inputContainer.value;
        const code = editor.getValue();
        const file_id = editorElement.dataset.file_id;
        const channel_id = document.body.dataset.channelId;

        fetch('/save-code/', {
            method: "POST",
            headers: {
                'Content-Type': 'application/json',
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
                alert(data.error);
            }
        });
    });

    // Load data button
    document.getElementById("load_data").addEventListener('click', () => {
        console.log('Clicked');
        const savedCode = localStorage.getItem(`${channel_id}_cod`);
        if (savedCode) {
            editor.setValue(savedCode);
        }
    });

    // Run code button
    const btn = document.getElementById('run-code');
    btn.addEventListener('click', function () {
        const code = editor.getValue();
        const code_executed_by = btn.dataset['executed'];
        const language = btn.dataset['language'];
        const inputs = "";

        console.log('language is: ', language);
        startTask(code, code_executed_by, inputs, language);
    });

    // Auto-save to local storage
    const save_code_in_local_storage = () => {
        let value = editor.getValue();
        console.log('Done');
        if (value) {
            localStorage.setItem(`${channel_id}_cod`, value);
        }
    };

    // File button active state
    document.addEventListener('DOMContentLoaded', function () {
        const fileButtons = document.querySelectorAll('.file-button');

        fileButtons.forEach(button => {
            button.addEventListener('click', function () {
                // Remove 'active' class from all buttons
                fileButtons.forEach(btn => btn.classList.remove('active'));

                // Add 'active' class to the clicked button
                this.classList.add('active');
            });
        });
    });
}

// ===== MAIN INITIALIZATION =====
require.config({ paths: { 'vs': 'https://cdn.jsdelivr.net/npm/monaco-editor/min/vs' } });

require(['vs/editor/editor.main'], function () {
    // Wait for DOM to be ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initializeApp);
    } else {
        initializeApp();
    }
});

function initializeApp() {
    console.log('Initializing application...');
    
    // Test basic DOM functionality
    console.log('Testing DOM functionality...');
    const testElement = document.createElement('div');
    testElement.style.display = 'none';
    document.body.appendChild(testElement);
    console.log('DOM manipulation test passed');
    
    // Initialize configuration first
    if (!initializeConfiguration()) {
        console.error('Failed to initialize configuration');
        return;
    }
    
    // Initialize all components
    try {
        initializeModal();
        initializeFileManagement();
        initializePasteHistory();
        initializeMembersPanel();
        initializeWebSockets();
        initializeEditor();
        console.log('Application initialized successfully');
        
        // Add a simple test click handler
        document.addEventListener('click', function(e) {
            console.log('Click detected on:', e.target);
        });
        
    } catch (error) {
        console.error('Error initializing application:', error);
    }
}