export type Item = {
	id: string | number;
	name: string;
};

export interface MultiComboboxProps {
	id?: string;
	label: string;
	description?: string;
	error?: string;
	items: string[];
	onValueChange: (values: string[]) => void;
	value: string[];
	containerClassName?: string;
	placeholder?: string;
	disabled?: boolean;
	addNewLabel?: string;
}
