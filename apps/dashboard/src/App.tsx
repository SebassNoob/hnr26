import { MemoryRouter, Routes, Route } from "react-router";
import { About, Configuration, NotFound } from "./app/index";

function Layout({ children }: { children: React.ReactNode }) {
	return (
		<main className="min-h-screen bg-gray-100 dark:bg-neutral-900">
			<div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">{children}</div>
		</main>
	);
}

const routes = {
	"/": <Configuration />,
	"/about": <About />,
	"*": <NotFound />,
};

function App() {
	return (
		<MemoryRouter initialEntries={["/"]} initialIndex={0}>
			<Routes>
				{Object.entries(routes).map(([path, element]) => (
					<Route key={path} path={path} element={<Layout>{element}</Layout>} />
				))}
			</Routes>
		</MemoryRouter>
	);
}

export default App;
