export default function ThinkingIndicator() {
	return (
		<div className="flex w-full items-end justify-start gap-2">
			<div className="h-7 w-7 shrink-0 rounded-full border border-[#CC0000] bg-white" />
			<div className="rounded-4xl rounded-bl-2xl border border-[#E0E0E0] bg-white px-5 py-4 shadow-sm">
				<div className="flex items-center gap-2">
					<span className="h-2.5 w-2.5 animate-[bounce_1.2s_ease-in-out_infinite] rounded-full bg-[#CC0000]" />
					<span className="h-2.5 w-2.5 animate-[bounce_1.2s_ease-in-out_0.15s_infinite] rounded-full bg-[#CC0000]" />
					<span className="h-2.5 w-2.5 animate-[bounce_1.2s_ease-in-out_0.3s_infinite] rounded-full bg-[#CC0000]" />
				</div>
			</div>
		</div>
	)
}
