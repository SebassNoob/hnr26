import { useForm, type SubmitHandler, Controller } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { TimePicker, Button, Text, MultiCombobox } from "@shared/ui";
import { useEffect, useEffectEvent } from "react";
import { configSchema, type Config } from "./configSchema";
import { Link } from "react-router";

type ConfigFormData = Config;

export function Configuration() {
	const {
		register,
		handleSubmit,
		control,
		formState: { errors, isSubmitting },
		reset,
	} = useForm<ConfigFormData>({
		resolver: zodResolver(configSchema),
		defaultValues: {
			lightsOutStart: "22:00",
			lightsOutEnd: "06:00",
			blacklistedProcesses: [],
			nag: [],
			slipperEnabled: false,
		},
	});

	useEffect(() => {
		loadConfig();
	}, []);

	const loadConfig = useEffectEvent(async () => {
		try {
			const result = await window.ipcRenderer.invoke("load-config");
			if (result.success) {
				reset(result.data);
				console.info("Config loaded:", result.data);
			}
		} catch (error) {
			console.error("Error loading config:", error);
		}
	});

	const onSubmit: SubmitHandler<ConfigFormData> = async (data) => {
		try {
			const result = await window.ipcRenderer.invoke("save-config", data);
			if (!result.success) {
				alert(`Failed to save configuration: ${result.error}`);
				return;
			}

			// launch with new config

			const execResult = await window.ipcRenderer.invoke("execute-urmom", [JSON.stringify(data)]);
			if (!execResult.success) {
				alert(`Failed to execute UrMom: ${execResult.stderr}`);
			} else {
				await window.ipcRenderer.invoke("close-window");
			}
		} catch (error) {
			console.error("Error saving config:", error);
			alert("Failed to save configuration");
		}
	};

	return (
		<div className="p-6">
			<div className="mb-6">
				<Text className="text-2xl font-bold">UrMom Launcher</Text>
				<Text description className="mt-1">
					Set your desired configuration options below and save to apply and launch UrMom. Read more
					about the application{" "}
					<span>
						<Link to="/about" className="text-blue-600 hover:underline">
							here
						</Link>
					</span>
					.
				</Text>
			</div>

			<form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
				<div>
					<Text className="text-sm/6 font-medium mb-1">Lights Out Time Range</Text>
					<Text description className="text-sm mb-2">
						Time range when your mother will shut your computer off.
					</Text>
					<div className="grid grid-cols-2 gap-4">
						<TimePicker
							label="Start Time"
							{...register("lightsOutStart")}
							error={errors.lightsOutStart?.message}
						/>
						<TimePicker
							label="End Time"
							{...register("lightsOutEnd")}
							error={errors.lightsOutEnd?.message}
						/>
					</div>
				</div>

				<Controller
					name="blacklistedProcesses"
					control={control}
					render={({ field }) => (
						<div>
							<div className="flex gap-2 items-end relative sm:flex-row flex-col ">
								<div className="flex-1">
									<MultiCombobox
										label="Blacklisted Processes"
										description="Enter distractions for your mom to block (e.g., chrome, steam)."
										placeholder="Type process name and press Enter or Add"
										items={[]}
										onValueChange={field.onChange}
										value={field.value}
										error={errors.blacklistedProcesses?.message}
									/>
								</div>
								<Button
									type="button"
									onClick={async () => {
										try {
											const filePath = await window.ipcRenderer.invoke("select-file");
											if (filePath) {
												field.onChange([...field.value, filePath]);
												console.info("Selected file:", filePath);
											}
										} catch (error) {
											console.error("Error selecting file:", error);
										}
									}}
									className="sm:absolute sm:top-0 sm:right-0 w-full sm:w-auto"
								>
									Browse
								</Button>
							</div>
						</div>
					)}
				/>

				<Controller
					name="nag"
					control={control}
					render={({ field }) => (
						<MultiCombobox
							label="Nag Messages"
							description="What messages should your mom use to nag you."
							placeholder="Type a message and press Enter or Add"
							items={[]}
							onValueChange={field.onChange}
							value={field.value}
							error={errors.nag?.message}
						/>
					)}
				/>

				<div className="flex items-center gap-3">
					<input
						type="checkbox"
						id="slipperEnabled"
						{...register("slipperEnabled")}
						className="size-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500 focus:ring-offset-0"
					/>
					<div>
						<label
							htmlFor="slipperEnabled"
							className="text-sm/6 font-medium text-black dark:text-zinc-200 cursor-pointer"
						>
							Enable Slipper Mode
						</label>
						<Text description className="text-sm">
							Your mom will use her slipper to hit you when you disobey.
						</Text>
					</div>
				</div>
				{errors.slipperEnabled && (
					<Text className="text-red-500 text-xs">{errors.slipperEnabled.message}</Text>
				)}

				<div className="pt-4">
					<Button type="submit" disabled={isSubmitting} className="w-full">
						{isSubmitting ? "Saving..." : "Save Configuration"}
					</Button>
				</div>

				{Object.keys(errors).length > 0 && (
					<div className="mt-4 p-3 bg-red-50 dark:bg-red-900/20 rounded-md">
						<Text className="text-red-600 dark:text-red-400 text-sm font-medium">
							Please fix the errors above
						</Text>
					</div>
				)}
			</form>
		</div>
	);
}
