import Image from 'next/image'

type BaymaxAvatarProps = {
  className?: string
}

export default function BaymaxAvatar({ className = '' }: BaymaxAvatarProps) {
  return (
    <div
      className={[
        'relative grid place-items-center rounded-full bg-[rgba(255,255,255,0.78)] shadow-[0_10px_28px_rgba(67,92,97,0.08)] backdrop-blur-sm',
        className,
      ].join(' ')}
    >
      <Image
        src="/baymax-face.svg"
        alt="Baymax avatar"
        fill
        sizes="48px"
        className="p-[19%] object-contain"
      />
    </div>
  )
}
