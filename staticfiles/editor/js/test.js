// const editor = CodeMirror.fromTextArea(document.getElementById("code"), {
//     lineNumbers: true,
//     mode: "javascript",
//     theme: "dracula", // change to other themes if needed
//     tabSize: 2,
//     indentWithTabs: false
// });

// const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
// const testSocket = new WebSocket(`${protocol}://` + window.location.host + '/ws/test-monitor/' + room_id + '/')



// // Optional: WebSocket event handlers
// testSocket.onopen = () => {
//   console.log("WebSocket connected to", testSocket.url);
// };

// testSocket.onmessage = (event) => {
//   const data = JSON.parse(event.data);
//   console.log("Received:", data);
// };

// testSocket.onclose = () => {
//   console.warn("WebSocket connection closed.");
// };

// testSocket.onerror = (error) => {
//   console.error("WebSocket error:", error);
// };