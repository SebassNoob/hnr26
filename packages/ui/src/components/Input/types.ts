import type { InputHTMLAttributes, ReactNode } from "react";

export interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
	label?: ReactNode;
	description?: ReactNode;
	error?: ReactNode;
	/** Optional icon to display inside the input, aligned to the right */
	icon?: ReactNode;
	/** Optional button to display inside the input, positioned absolutely */
	button?: ReactNode;
	className?: string;
	containerClassName?: string;
}
