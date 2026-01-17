import { z } from "zod";

// Shared config validation schema used by renderer and main process
export const timeRegex = /^([0-1][0-9]|2[0-3]):[0-5][0-9]$/;

export const configSchema = z.object({
	lightsOutStart: z.string().regex(timeRegex, "Must be in format HH:mm (e.g., 22:00)"),
	lightsOutEnd: z.string().regex(timeRegex, "Must be in format HH:mm (e.g., 06:00)"),
	blacklistedProcesses: z.array(z.string()).min(1, "At least one process is required"),
	nag: z.array(z.string()).min(1, "At least one nag message is required"),
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
		"Get back to work!",
		"Your mom is watching you!",
		"No more games until chores are done!",
		"Focus on your studies!",
		"Time to take a break from the screen!",
		"Remember why your mom set this up!",
		"Don't make your mom angry!",
		"Work now, play later!",
		"Your future self will thank you!",
		"Distractions won't help you succeed!",
		"Stay focused and be productive!",
		"Keep your priorities straight!",
		"Your mom believes in you!",
		"Make her proud!",
	],
	slipperEnabled: false,
};
