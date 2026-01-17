import { Title, Text } from "@shared/ui";
import { Link } from "react-router";

export function About() {
	return (
		<div className="p-6 w-full">
			<div className="mb-4">
				<Title className="text-2xl font-bold text-black dark:text-white">UrMom Launcher</Title>
				<Text className="mt-1" description>
					UrMom is an application to simulate a stereotypical asian mother nagging you.
				</Text>
			</div>
			<div className="mb-4">
				<Title className="text-xl font-bold text-black dark:text-white mt-6">Features</Title>
				<ul className="list-disc list-inside mt-2 text-gray-600 dark:text-gray-400">
					<li>Closes irrelevant apps</li>
					<li>Schedule "lights out" time to force shutdown your computer.</li>
          <li>Nags at you.</li>
				</ul>
			</div>

			<Link to="/" className=" text-blue-500 hover:underline ">
				Go back to Dashboard
			</Link>
		</div>
	);
}
