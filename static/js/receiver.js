let subscriptionKey;
let serviceRegion = "eastasia";
let authorizationToken = "";
let SpeechSDK;
let synthesizer;
let player;
let audioConfig;
let ttsToken;
let speechCounter = 0;
let recognizer;
let targetLanguageAbb;
let speechConfig;
let spokenData = [];

function intialize() {
  console.log("initialize");
  var myModal = new bootstrap.Modal(document.getElementById("exampleModal"));
  myModal.show();

  //CHECKING BROWSER SINCE AZURE NOT WORKING ON ALL BROWSERS
  if (
    (navigator.userAgent.indexOf("Opera") ||
      navigator.userAgent.indexOf("OPR")) != -1
  ) {
    alert("This browser is not supported. You need to use CHROME");
  } else if (navigator.userAgent.indexOf("Chrome") != -1) {
  } else if (navigator.userAgent.indexOf("Safari") != -1) {
    alert("This browser is not supported. You need to use CHROME");
  } else if (navigator.userAgent.indexOf("Firefox") != -1) {
    alert("This browser is not supported. You need to use CHROME");
  } else if (
    navigator.userAgent.indexOf("MSIE") != -1 ||
    !!document.documentMode == true
  ) {
    alert("This browser is not supported. You need to use CHROME");
  } else {
    alert("This browser is not supported. You need to use CHROME");
  }

  if (!!window.SpeechSDK) {
    SpeechSDK = window.SpeechSDK;
    ttsButtonState = "starting";
  } else {
    ttsButtonState = "error";
    console.log("error with SpeechSDK", !!window.SpeechSDK);
  }
}

function initializeService(TL) {
  if (ttsToken) {
    speechConfig = SpeechSDK.SpeechTranslationConfig.fromAuthorizationToken(
      ttsToken,
      "eastus"
    );
  } else {
    subscriptionKey = "6af6abea507a4e09ae379b22e79ef25a";
    speechConfig = SpeechSDK.SpeechConfig.fromSubscription(
      subscriptionKey,
      "eastus"
    );
  }

  try {
    speechConfig.speechSynthesisLanguage = TL.split(" ")[0];
    speechConfig.speechSynthesisVoiceName = TL.split(" ")[1];
  } catch (error) {
    console.log(error);
  }

  synthesizer = new SpeechSDK.SpeechSynthesizer(speechConfig);
}

async function speak(inputText, targetLanguageAbb, voiceSpeed) {
  console.log("Inizialising config");
  console.log("Speaking: " + inputText);
  console.log("in lang: " + targetLanguageAbb);

  var voices = {
    en: "en-US-SteffanNeural",
    es: "es-ES-AlvaroNeural",
    it: "it-IT-IsabellaNeural",
    he: "he-IL-AvriNeural",
    ar: "ar-EG-SalmaNeural",
    fr: "fr-FR-AlainNeural",
    pt: "pt-BR-FranciscaNeural",
    fa: "fa-IR-DilaraNeural",
    ja: "ja-JP-NanamiNeural",
    de: "de-DE-KatjaNeural",
  };

  var voiceType = voices[targetLanguageAbb];

  var voiceStyle = "general";
  console.log("voice type: " + voiceType);
  console.log("voice style: " + voiceStyle);
  console.log("voice speed: " + voiceSpeed);

  const ssml = `<speak xmlns="http://www.w3.org/2001/10/synthesis" xmlns:mstts="http://www.w3.org/2001/mstts" xmlns:emo="http://www.w3.org/2009/10/emotionml" version="1.0" xml:lang="${targetLanguageAbb}">
  <voice name="${voiceType}">
  <mstts:express-as style="${voiceStyle}">
  <prosody rate="${voiceSpeed}%" pitch="0%">
  ${inputText}
  </prosody>
  </mstts:express-as>
  </voice>
  </speak>`;

  await synthesizer.speakSsmlAsync(
    ssml,
    (result) => {
      if (result.errorDetails) {
        console.error(result.errorDetails);
      } else {
        console.log(JSON.stringify(result));       
      }
    },
    function (err) {
      startSpeakTextAsyncButton.disabled = false;
      document.getElementById("log").innerHTML = "Error: ";
      document.getElementById("log").innerHTML = err;
      document.getElementById("log").innerHTML = "\n";
      window.console.log(err);
    }
  );
}

function getConfig() {
  let codeId = document.getElementById("code-id").value;
  let selectedLanguage = document.getElementById("selected-lang").value;
  document.getElementById("sessionId").setAttribute("value", codeId);
  document.getElementById("sessionId").innerHTML = codeId;
  document
    .getElementById("targetLanguage")
    .setAttribute("value", selectedLanguage);
  document.getElementById("targetLanguage").innerHTML = selectedLanguage;
}
