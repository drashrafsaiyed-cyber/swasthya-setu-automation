const TELEGRAM_TOKEN = "PASTE-YOUR-TELEGRAM-BOT-TOKEN-HERE";
const SHEET_NAME = "Form Responses 1";
const STATE_KEY = "last_update_id";

function doPost(e) {
  try {
    const payload = JSON.parse(e.postData.contents || "{}");
    if (!payload.message) return ok_("no message");

    const updateId = payload.update_id;
    const lastId = Number(PropertiesService.getScriptProperties().getProperty(STATE_KEY) || 0);
    if (updateId <= lastId) return ok_("duplicate update");

    PropertiesService.getScriptProperties().setProperty(STATE_KEY, String(updateId));

    const messageText = payload.message.text || "";
    const chatId = payload.message.chat && payload.message.chat.id;
    if (!messageText || !chatId) return ok_("no text");

    const parsed = parseLabMessage(messageText.trim());
    if (!parsed) {
      sendMsg(
        chatId,
        "⚠️ Send details in one of these formats:\n" +
          "• Name, Age, Gender, BloodGroup\n" +
          "• Name Age Gender BloodGroup\n" +
          "Example: Sanila Saiyed, 38, Female, B+"
      );
      return ok_("bad format");
    }

    const { name, age, gender, blood } = parsed;
    const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(SHEET_NAME);
    if (!sheet) {
      sendMsg(chatId, "⚠️ Sheet not found. Please verify the sheet name in the script.");
      return ok_("sheet missing");
    }
    const data = sheet.getDataRange().getValues();

    let updated = false;
    for (let row = 1; row < data.length; row++) {
      const rowName = String(data[row][1] || "").trim().toLowerCase();
      const rowAge = String(data[row][2] || "").trim();
      const rowGender = String(data[row][3] || "").trim().toLowerCase();
      if (rowName === name.toLowerCase() && rowAge === age && rowGender === gender) {
        const currentBG = String(data[row][6] || "").trim().toUpperCase();
        if (currentBG === blood) {
          sendMsg(chatId, `ℹ️ Blood group already recorded for ${name}: ${currentBG}`);
        } else {
          sheet.getRange(row + 1, 7).setValue(blood);
          sendMsg(chatId, `✅ Updated: ${name} → ${blood}`);
        }
        updated = true;
        break;
      }
    }

    if (!updated) {
      sendMsg(chatId, `❌ No matching record found for ${name} (${age}, ${gender}).`);
    }
  } catch (error) {
    Logger.log(error);
  }

  return ok_("done");
}

function parseLabMessage(message) {
  const commaParts = message
    .split(/\s*,\s*/)
    .map((part) => part.trim())
    .filter(Boolean);
  if (commaParts.length >= 4) {
    return normaliseLabParts(commaParts[0], commaParts[1], commaParts[2], commaParts[3]);
  }

  const spaceParts = message
    .split(/[\s]+/)
    .map((part) => part.trim())
    .filter(Boolean);
  if (spaceParts.length >= 4) {
    const blood = spaceParts.pop();
    const gender = spaceParts.pop();
    const age = spaceParts.pop();
    const name = spaceParts.join(" ");
    return normaliseLabParts(name, age, gender, blood);
  }
  return null;
}

function normaliseLabParts(name, ageRaw, genderRaw, bloodRaw) {
  const cleanedName = name.replace(/\s+/g, " ").trim();
  if (!cleanedName) return null;

  const age = ageRaw.replace(/[^0-9]/g, "");
  if (!age) return null;

  const genderLower = genderRaw.toLowerCase();
  let gender = "";
  if (["male", "m"].includes(genderLower)) {
    gender = "male";
  } else if (["female", "f"].includes(genderLower)) {
    gender = "female";
  } else {
    gender = genderLower.replace(/[^a-z]/g, "");
  }
  if (!gender) return null;

  const blood = bloodRaw.toUpperCase().replace(/[^ABO\-+]/g, "");
  if (!blood) return null;

  return {
    name: cleanedName,
    age: age,
    gender: gender,
    blood: blood,
  };
}

function sendMsg(chatId, text) {
  if (!TELEGRAM_TOKEN || TELEGRAM_TOKEN === "PASTE-YOUR-TELEGRAM-BOT-TOKEN-HERE") {
    Logger.log("Missing TELEGRAM_TOKEN value. Update TELEGRAM_TOKEN in the script.");
    return;
  }
  const url = `https://api.telegram.org/bot${TELEGRAM_TOKEN}/sendMessage`;
  UrlFetchApp.fetch(url, {
    method: "post",
    contentType: "application/json",
    payload: JSON.stringify({
      chat_id: chatId,
      text: text,
    }),
    muteHttpExceptions: true,
  });
}

function ok_(text) {
  return ContentService.createTextOutput(text);
}

function setWebhook() {
  const url = ScriptApp.getService().getUrl();
  const webhookUrl = `https://api.telegram.org/bot${TELEGRAM_TOKEN}/setWebhook?url=${url}`;
  const resp = UrlFetchApp.fetch(webhookUrl);
  Logger.log(resp.getContentText());
}

function onFormSubmit(e) {
  if (!e || !e.range) {
    Logger.log("onFormSubmit called without event data");
    return;
  }

  const sheet = e && e.source ? e.source.getSheetByName(SHEET_NAME) : SpreadsheetApp.getActiveSpreadsheet().getSheetByName(SHEET_NAME);
  if (!sheet) {
    Logger.log("Sheet not found while generating member ID. Check SHEET_NAME constant.");
    return;
  }
  const row = e.range.getRow();
  if (row === 1) return;

  const idColumn = 10;
  const idCell = sheet.getRange(row, idColumn);
  if (!idCell.getValue()) {
    const uniqueId = generateUniqueMemberId(sheet);
    idCell.setValue(uniqueId);
  }
}

function generateUniqueMemberId(sheet) {
  const prefix = "SS-";
  const dateCode = Utilities.formatDate(new Date(), "GMT+5:30", "yyMMdd");
  let uniqueId;
  const existing = new Set(
    sheet
      .getRange(2, 10, Math.max(sheet.getLastRow() - 1, 0), 1)
      .getValues()
      .flat()
      .filter(Boolean)
      .map(String)
  );

  do {
    const randomPart = Math.random().toString(36).substring(2, 8).toUpperCase();
    const randomSuffix = Math.random().toString(36).substring(2, 6).toUpperCase();
    uniqueId = `${prefix}${dateCode}-${randomPart}-${randomSuffix}`;
  } while (existing.has(uniqueId));

  return uniqueId;
}
