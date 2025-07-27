$(document).ready(function () {
  // Toggle join channel form
  $("#joinChannelBtn").click(function () {
    $("#joinChannelForm").removeClass("d-none");
    $(this).hide();
  });

  $("#cancelJoinBtn").click(function () {
    $("#joinChannelForm").addClass("d-none");
    $("#joinChannelBtn").show();
  });

  // Toggle create channel form
  $("#create-channel").click(function () {
    $("#channel-form").slideToggle(300);
  });

  $("#cancelChannelBtn").click(function () {
    $("#channel-form").slideUp(300);
  });

  // Handle form submission for joining channel
  $("#joinChannelFormElement").submit(function (event) {
    event.preventDefault();
    const roomId = $("#room-id").val().trim();

    if (roomId) {
      window.location.href = `/join-channel/${roomId}/`;
    } else {
      alert("Please enter a valid Room ID");
    }
  });

  // Auto-scroll chat to bottom
  const chatBody = document.getElementById("chat-body");
  chatBody.scrollTop = chatBody.scrollHeight;

  // Handle Enter key in message input
  $("#messageInput").keypress(function (e) {
    if (e.which === 13) {
      sendMessage();
    }
  });
});

const user = document.body.dataset.user;
const userImage = document.body.dataset.userImage;
const userId = document.body.dataset.userId;
// WebSocket for global chat
const protocol = window.location.protocol === "https:" ? "wss" : "ws";
const chat_socket = new WebSocket(
  `${protocol}://` + window.location.host + "/ws/global-chat/" + user + "/"
);

chat_socket.onmessage = function (e) {
  const data = JSON.parse(e.data);
  const messageText = data.message;
  const sender = data.sender;
  const userImage =
    data.userImage ||
    "https://www.pngplay.com/wp-content/uploads/12/User-Avatar-Profile-PNG-Free-File-Download.png";
  const messageTime = data.time;

  // Create message element with animation
  const newMessage = document.createElement("div");
  newMessage.classList.add("chat-message", "new-message");
  newMessage.innerHTML = `
        <img src="${userImage}" alt="${sender}" class="user-image">
        <div class="message-content">
          <div class="user-info">
            <span class="user">${sender}</span>
            <span class="message-time">${messageTime}</span>
          </div>
          <div class="message-text">${messageText}</div>
        </div>
      `;

  // Append to chat body
  const chatBody = document.getElementById("chat-body");
  chatBody.appendChild(newMessage);

  // Remove animation class after it completes
  setTimeout(() => {
    newMessage.classList.remove("new-message");
  }, 500);

  // Scroll to bottom
  chatBody.scrollTop = chatBody.scrollHeight;
};

chat_socket.onclose = function (e) {
  console.error("WebSocket closed unexpectedly");
  // Show reconnect button or notification
};

chat_socket.onerror = function (e) {
  console.error("WebSocket error observed:", e);
};

function sendMessage() {
  const messageInput = document.getElementById("messageInput");
  const messageText = messageInput.value.trim();

  if (!messageText) {
    // Add visual feedback for empty message
    messageInput.classList.add("is-invalid");
    setTimeout(() => {
      messageInput.classList.remove("is-invalid");
    }, 1000);
    return;
  }

  const current_user = document.getElementById("send_btn").dataset["user"];
  var d = new Date();

  // Add sending animation to button
  const sendBtn = document.getElementById("send_btn");
  sendBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
  sendBtn.disabled = true;

  chat_socket.send(
    JSON.stringify({
      message: messageText,
      sender: current_user,
      userImage: "{{userprofile.imageURL}}",
      user_id: "{{userprofile.id}}",
      time: d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    })
  );

  // Reset button and input
  setTimeout(() => {
    sendBtn.innerHTML = '<i class="fas fa-paper-plane"></i>';
    sendBtn.disabled = false;
  }, 500);

  messageInput.value = "";
  messageInput.focus();
}
