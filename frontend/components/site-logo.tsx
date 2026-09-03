import Link from "next/link";

type SiteLogoProps = {
  className?: string;
};

export function SiteLogo({ className = "" }: SiteLogoProps) {
  return (
    <Link
      aria-label="EventEveryday home"
      className={`site-logo ${className}`.trim()}
      href="/"
    >
      <svg aria-hidden="true" focusable="false" role="img" viewBox="0 0 360 84">
        <rect fill="#ed784e" height="68" rx="20" width="68" x="2" y="2" />
        <path
          d="M47 22c-4-3-9-5-14-3-7 2-11 9-11 17v1c0 10 5 18 13 19 6 1 11-1 15-5M24 37h22M28 27h15M28 48h16"
          fill="none"
          stroke="#fffdf8"
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth="5.5"
        />
        <text x="82" y="58">EventEveryday</text>
      </svg>
    </Link>
  );
}
