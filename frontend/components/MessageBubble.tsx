import type { Message } from '@/lib/api'

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
				'flex w-full items-end gap-2',
				isUser ? 'justify-end' : 'justify-start',
			].join(' ')}
		>
			{!isUser && (
				<div className="h-7 w-7 shrink-0 rounded-full border border-[#CC0000] bg-white" />
			)}

			<div
				className={[
					'max-w-[85%] whitespace-pre-wrap px-5 py-3 text-[15px] leading-7 shadow-sm sm:max-w-[72%]',
					isUser
						? 'rounded-[999px] rounded-br-2xl bg-[#CC0000] text-white'
						: 'rounded-4xl rounded-bl-2xl border border-[#E0E0E0] bg-white text-[#1A1A1A]',
				].join(' ')}
			>
				{message.content}
				{showStreamingCursor && (
					<span className="ml-1 inline-block h-5 w-0.75 animate-pulse rounded-full bg-[#CC0000] align-middle" />
				)}
			</div>
		</div>
	)
}
