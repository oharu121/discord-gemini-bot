// Google Apps Script - Keep HF Space Alive
// Set up a time-based trigger to run every 10 minutes
//
// Setup Instructions:
// 1. Go to script.google.com
// 2. Create new project
// 3. Paste this code
// 4. Replace YOUR_USERNAME and YOUR_SPACE_NAME below
// 5. Go to Triggers (clock icon) > Add Trigger
// 6. Choose: keepAlive, Time-driven, Minutes timer, Every 10 minutes
// 7. Save and authorize

function keepAlive() {
  // Replace with your actual HF Space URL
  const SPACE_URL = "https://YOUR_USERNAME-YOUR_SPACE_NAME.hf.space/";

  try {
    const response = UrlFetchApp.fetch(SPACE_URL, {
      method: "GET",
      muteHttpExceptions: true,
      followRedirects: true
    });

    const code = response.getResponseCode();
    Logger.log("Keep-alive ping: " + code + " at " + new Date().toISOString());

    if (code >= 400) {
      Logger.log("Warning: Space may be down or sleeping");
    }
  } catch (error) {
    Logger.log("Keep-alive error: " + error.message);
  }
}

// Optional: Test function to verify setup
function testKeepAlive() {
  keepAlive();
  Logger.log("Test complete - check Logs (View > Logs)");
}
