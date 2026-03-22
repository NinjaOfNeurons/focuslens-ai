import { startLandmarkSender } from "./landmark-sender.js";

const video  = document.getElementById("webcam");
const status = document.getElementById("status");

startLandmarkSender(video, msg => { status.textContent = msg; });