/**
 * PollToll mark: two overlapping rolls (old and new) with the verified
 * overlap in the middle. Vector version of the brand logo so it stays
 * sharp at every size.
 */
export default function Logo({
  className = "",
  title = "PollToll",
}: {
  className?: string;
  title?: string;
}) {
  return (
    <svg viewBox="18 -3.5 300 300" role="img" aria-label={title} className={className}>
      <path
        d="M168 65.4 A92.5 92.5 0 0 1 168 227.6 A92.5 92.5 0 0 1 168 65.4 Z"
        fill="#DEA651"
      />
      <circle cx="123.5" cy="146.5" r="92.5" fill="none" stroke="#8FC2B8" strokeWidth="18" />
      <circle cx="212.5" cy="146.5" r="92.5" fill="none" stroke="#F6F3ED" strokeWidth="18" />
      <path
        d="M149 147 L165 163.5 L193 126"
        fill="none"
        stroke="#121B2C"
        strokeWidth="15"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}
