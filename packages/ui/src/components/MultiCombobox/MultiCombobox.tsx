"use client";
import { XMarkIcon } from "@heroicons/react/24/outline";
import { useState } from "react";
import { Input, Text } from "..";
import type { MultiComboboxProps } from "./types";

export function MultiCombobox({
	id,
	label,
	description,
	error,
	onValueChange,
	value,
	containerClassName,
	placeholder,
	disabled,
	addNewLabel = "Add",
}: Readonly<MultiComboboxProps>) {
	const [query, setQuery] = useState("");

	const handleAddValue = () => {
		if (query.trim() && !value.includes(query.trim())) {
			onValueChange([...value, query.trim()]);
			setQuery("");
		}
	};

	const handleRemoveValue = (valueToRemove: string) => {
		onValueChange(value.filter((v) => v !== valueToRemove));
	};

	const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
		if (e.key === "Enter") {
			e.preventDefault();
			handleAddValue();
		}
	};

	return (
		<div className={containerClassName}>
			<Input
				id={id}
				label={label}
				description={description}
				error={error}
				type="text"
				value={query}
				onChange={(e) => setQuery(e.target.value)}
				onKeyDown={handleKeyDown}
				placeholder={placeholder}
				disabled={disabled}
				className="pr-16"
				button={
					<button
						type="button"
						onClick={handleAddValue}
						disabled={disabled || !query.trim()}
						className="m-0.5 px-3 py-1 flex items-center justify-center rounded text-xs font-medium focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 bg-blue-500 text-white hover:bg-blue-600 focus-visible:ring-blue-500 disabled:opacity-50 disabled:hover:bg-blue-500 disabled:cursor-not-allowed transition"
					>
						{addNewLabel}
					</button>
				}
			/>

			{value.length > 0 && (
				<div className="flex flex-wrap gap-2 mt-2">
					{value.map((val) => (
						<div
							key={val}
							className="flex items-center gap-1 px-2 py-1 rounded-md bg-blue-100 dark:bg-blue-900/30"
						>
							<Text className="text-blue-800 dark:text-blue-200 text-sm">{val}</Text>
							<button
								type="button"
								onClick={() => handleRemoveValue(val)}
								disabled={disabled}
								className="hover:bg-blue-200 dark:hover:bg-blue-800/50 rounded-full p-0.5 transition disabled:cursor-not-allowed cursor-pointer"
								aria-label={`Remove ${val}`}
							>
								<XMarkIcon className="size-3 stroke-2 text-blue-800 dark:text-blue-200" />
							</button>
						</div>
					))}
				</div>
			)}
		</div>
	);
}
