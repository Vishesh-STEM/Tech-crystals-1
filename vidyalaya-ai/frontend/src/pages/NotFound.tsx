import { Link } from "react-router-dom";
import { Compass } from "lucide-react";

export default function NotFound() {
  return (
    <div className="grid min-h-screen place-items-center bg-ink-50 px-4 dark:bg-ink-950">
      <div className="card max-w-md p-8 text-center">
        <Compass className="mx-auto mb-3 text-brand-500" size={34} />
        <h1 className="font-display text-2xl font-semibold text-ink-900 dark:text-white">Page not found</h1>
        <p className="muted mt-2">
          That page is not part of Vidyalaya AI. Head back to your dashboard and keep studying.
        </p>
        <Link to="/dashboard" className="btn-primary mt-5 inline-flex">
          Go to dashboard
        </Link>
      </div>
    </div>
  );
}
