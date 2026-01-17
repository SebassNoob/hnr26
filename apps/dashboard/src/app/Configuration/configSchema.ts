import { z } from "zod";

// Shared config validation schema used by renderer and main process
export const timeRegex = /^([0-1][0-9]|2[0-3]):[0-5][0-9]$/;

export const configSchema = z.object({
	lightsOutStart: z.string().regex(timeRegex, "Must be in format HH:mm (e.g., 22:00)"),
	lightsOutEnd: z.string().regex(timeRegex, "Must be in format HH:mm (e.g., 06:00)"),
	blacklistedProcesses: z.array(z.string()).min(1, "At least one process is required"),
	nag: z.array(z.string()).min(1, "At least one nag message is required"),
	screenshotFreqMin: z.number().min(1).max(60).optional(),
	slipperEnabled: z.boolean(),
});

export type Config = z.infer<typeof configSchema>;

export const defaultConfig: Config = {
	lightsOutStart: "22:00",
	lightsOutEnd: "06:00",
	blacklistedProcesses: [
		"minecraft.exe",
		"steam.exe",
		"epicgameslauncher.exe",
		"cs2.exe",
		"osu.exe",
	],
	nag: [
		"Don't think I don't know what you doing ah. My eyes everywhere one.",
		"Focus on your studying... then you can get good job in the future.",
		"Better finish your work first then play hor.",
		"Now you lazy, next time you regret then you know. Don't say I never warn you.",
		"When you finish this exam, I bring you go eat the Haidilao you like, okay?",
		"Wah, today so hardworking ah? Good lah, like that then is my child.",
		"My friend say her son very hardworking, I tell her 'My one also quite smart eh!'",
		"Aiyah, actually you quite smart one, just lazy only. Don't waste your brain leh.",
		"Do your best lah, so people won't say I don't know how to teach my own child.",
		"Now you discipline a bit, next time you don't need to work so hard like me.",
	],
	screenshotFreqMin: 5,
	slipperEnabled: false,
};
