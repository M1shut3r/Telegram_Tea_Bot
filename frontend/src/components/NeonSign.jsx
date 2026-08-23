export default function NeonSign({ compact = false }) {
  return (
    <div className={compact ? 'neon-frame px-3 py-2' : 'neon-frame'}>
      <p className={compact ? 'neon-sign text-[1.15rem]' : 'neon-sign'}>ЖИЛИПИЛИ</p>
    </div>
  )
}
