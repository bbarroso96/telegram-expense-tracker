// A friendly pill gauge: a single flat fill whose width = percent used and
// whose colour encodes status (ok / warn / over). No gradients, no ticks.
// `big` renders the taller Overall variant.
export default function Gauge({ width, status, big = false }) {
  return (
    <div className={big ? 'zbar' : 'track'}>
      <div className={'fill g-' + status} style={{ width: Math.min(width, 100) + '%' }} />
    </div>
  )
}
