import { Title, Text } from "@shared/ui";
import { Link } from "react-router";

export function NotFound() {
	return (
		<div className="flex flex-col items-center justify-center h-full">
			<Title>Page Not Found</Title>
			<Text className="mt-4 text-center">You shouldn't be here!</Text>
			<Link to="/" className="mt-6 text-blue-500 hover:underline">
				Go back to Dashboard
			</Link>
		</div>
	);
}
