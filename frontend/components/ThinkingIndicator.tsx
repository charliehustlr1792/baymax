import BaymaxAvatar from '@/components/BaymaxAvatar'

export default function ThinkingIndicator() {
	return (
		<div className="animate-rise flex w-full items-end justify-start gap-3">
			<BaymaxAvatar className="h-10 w-10 shrink-0 border border-[var(--border)]" />
			<div className="rounded-[30px] rounded-bl-[12px] border border-[var(--border)] bg-[var(--surface-strong)] px-5 py-4 shadow-[0_18px_42px_rgba(67,92,97,0.08)] backdrop-blur-sm">
				<div className="flex items-center gap-2">
					<span className="h-2.5 w-2.5 animate-[bounce_1.2s_ease-in-out_infinite] rounded-full bg-[var(--accent)]" />
					<span className="h-2.5 w-2.5 animate-[bounce_1.2s_ease-in-out_0.15s_infinite] rounded-full bg-[var(--accent)]" />
					<span className="h-2.5 w-2.5 animate-[bounce_1.2s_ease-in-out_0.3s_infinite] rounded-full bg-[var(--accent)]" />
				</div>
			</div>
		</div>
	)
}