import { Field, Label, Input as HeadlessInput, Description } from "@headlessui/react";
import { twMerge } from "tailwind-merge";
import type { TimePickerProps } from "./types";

const baseInput =
	"block w-full rounded-sm border-none bg-slate-950/5 dark:bg-white/5 px-3 py-1.5 text-sm/6 dark:text-white text-black [&::-webkit-calendar-picker-indicator]:hidden [&::-webkit-inner-spin-button]:hidden [&::-webkit-clear-button]:hidden";
const focusInput = "focus:outline-2 focus:outline-blue-500";

export function TimePicker({
	label,
	description,
	error,
	id,
	className,
	containerClassName,
	...rest
}: TimePickerProps) {
	const inputClass = twMerge(
		baseInput,
		focusInput,
		error ? "outline-red-500 outline-1" : "",
		"pr-10",
		className,
	);

	return (
		<div className={containerClassName}>
			<Field className="flex flex-col gap-1">
				<div className="flex flex-col gap-0.5">
					{label && (
						<Label
							as="label"
							htmlFor={id}
							className="text-sm/6 font-medium text-black dark:text-zinc-200"
						>
							{label}
						</Label>
					)}
					{description && (
						<Description className="text-gray-600 dark:text-gray-400 text-sm">
							{description}
						</Description>
					)}
				</div>

				<div className="relative">
					<HeadlessInput id={id} as="input" type="time" className={inputClass} {...rest} />
					<span className="pointer-events-none absolute inset-y-0 right-3 flex items-center">
						<svg
							className="w-4 h-4 text-gray-500 dark:text-gray-400"
							aria-hidden="true"
							xmlns="http://www.w3.org/2000/svg"
							width="24"
							height="24"
							fill="none"
							viewBox="0 0 24 24"
						>
							<path
								stroke="currentColor"
								strokeLinecap="round"
								strokeLinejoin="round"
								strokeWidth="2"
								d="M12 8v4l3 3m6-3a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z"
							/>
						</svg>
					</span>
				</div>

				{error && <Description className="text-red-500 text-xs">{error}</Description>}
			</Field>
		</div>
	);
}
