import { MemoryRouter, Routes, Route } from "react-router";
import { About, Configuration, NotFound } from "./app/index";

function Layout({ children }: { children: React.ReactNode }) {
	return (
		<div className="min-h-screen bg-gray-100 dark:bg-neutral-900">
			<header className="bg-white shadow">
				<div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
					<h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
				</div>
			</header>
			<main>
				<div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">{children}</div>
			</main>
		</div>
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
