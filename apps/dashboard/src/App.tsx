import { BrowserRouter, Routes, Route } from "react-router";
import { About, Configuration, NotFound } from "./app";

function App() {
	return (
		<BrowserRouter>
			<Routes>
				<Route path="/" element={<Configuration />} />
				<Route path="/about" element={<About />} />
				<Route path="*" element={<NotFound />} />
			</Routes>
		</BrowserRouter>
	);
}

export default App;
