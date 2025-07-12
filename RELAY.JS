<!DOCTYPE html>
<html>
<head>
  <title>Relay Client Connect</title>
  <script src="https://unpkg.com/@signalwire/js"></script>
</head>
<body>
  <h2>Connecting to SignalWire Relay...</h2>
  <script>
    async function connectRelay() {
      try {
        // Fetch JWT token from your Flask backend
        const response = await fetch("http://localhost:5000/generate-token");
        const data = await response.json();
        const jwt = data.token;

        // Connect to Relay
        const client = await SignalWire.RelayClient({
          project: "d286373f-ba37-4896-a195-555d106fbfd8",
          token: jwt,
          host: "voiceaicall.signalwire.com"
        });

        await client.connect();

        console.log("✅ Connected to Relay!");
        // Optional: subscribe to incoming events
        client.on('message.received', (msg) => {
          console.log("📩 Message received:", msg);
        });

      } catch (err) {
        console.error("❌ Error connecting:", err);
      }
    }

    connectRelay();
  </script>
</body>
</html>
