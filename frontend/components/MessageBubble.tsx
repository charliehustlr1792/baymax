import type { Message } from '@/lib/api'
import BaymaxAvatar from '@/components/BaymaxAvatar'

type MessageBubbleProps = {
	message: Message
	showStreamingCursor?: boolean
}

export default function MessageBubble({
	message,
	showStreamingCursor = false,
}: MessageBubbleProps) {
	const isUser = message.role === 'user'

	return (
		<div
			className={[
				'animate-rise flex w-full items-end gap-3',
				isUser ? 'justify-end' : 'justify-start',
			].join(' ')}
		>
			{!isUser && (
				<BaymaxAvatar className="h-10 w-10 shrink-0 border border-[var(--border)]" />
			)}

			<div
				className={[
					'max-w-[88%] whitespace-pre-wrap px-5 py-4 text-[15px] leading-7 shadow-[0_18px_42px_rgba(67,92,97,0.08)] backdrop-blur-sm sm:max-w-[72%]',
					isUser
						? 'rounded-[30px] rounded-br-[12px] bg-[linear-gradient(135deg,#baa48c_0%,#9e866f_100%)] text-white'
						: 'rounded-[30px] rounded-bl-[12px] border border-[var(--border)] bg-[var(--surface-strong)] text-[var(--foreground)]',
				].join(' ')}
			>
				{message.content}
				{showStreamingCursor && (
					<span className="ml-1 inline-block h-5 w-0.5 animate-pulse rounded-full bg-[var(--accent-strong)] align-middle" />
				)}
			</div>
		</div>
	)
}