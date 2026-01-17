import type { InputHTMLAttributes, ReactNode } from "react";

export interface TimePickerProps extends Omit<InputHTMLAttributes<HTMLInputElement>, "type"> {
	label?: ReactNode;
	description?: ReactNode;
	error?: ReactNode;
	className?: string;
	containerClassName?: string;
}
