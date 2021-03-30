import Link from 'next/link';

export default function Layout({ children, href, className }) {
  return (
    <Link href={href}>
      <div
        className={`px-6 pt-3 pb-4 text-base text-center rounded-lg cursor-pointer md:text-xl lg:w-1/6 lg:transition lg:duration-300 ${className}`}
      >
        {children}
      </div>
    </Link>
  );
}
