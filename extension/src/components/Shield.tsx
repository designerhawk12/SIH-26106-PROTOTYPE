interface Props {
  verdict: "clean" | "suspicious";

  authentication: {
    spf: string;
    dkim: string;
    dmarc: string;
  };
}

function StatusRow({ label, value }: { label: string; value: string }) {
  const passed = value.toLowerCase() === "pass";

  return (
    <div
      className="
      flex
      items-center
      justify-between
      border-b
      border-zinc-800
      py-2
      last:border-b-0
    "
    >
      <span className="text-xs text-zinc-500">{label}</span>

      <span
        className={
          passed
            ? "text-xs font-semibold text-emerald-400"
            : "text-xs font-semibold text-red-400"
        }
      >
        {passed ? "✓ PASS" : value.toUpperCase()}
      </span>
    </div>
  );
}

export default function Shield({ verdict, authentication }: Props) {
  const clean = verdict === "clean";

  return (
    <div
      className={
        clean
          ? `
            rounded-xl
            border
            border-emerald-900/70
            bg-emerald-950/30
            p-4
            shadow-[0_0_30px_rgba(16,185,129,0.08)]
          `
          : `
            rounded-xl
            border
            border-orange-900/70
            bg-orange-950/30
            p-4
            shadow-[0_0_30px_rgba(249,115,22,0.08)]
          `
      }
    >
      <div className="mb-3 flex items-center gap-3">
        <div
          className={
            clean
              ? "flex h-10 w-10 items-center justify-center rounded-full bg-emerald-500/10 text-xl text-emerald-400"
              : "flex h-10 w-10 items-center justify-center rounded-full bg-orange-500/10 text-xl text-orange-400"
          }
        >
          {clean ? "✓" : "!"}
        </div>

        <div>
          <p
            className={
              clean ? "font-bold text-emerald-400" : "font-bold text-orange-400"
            }
          >
            {clean ? "Email Looks Clean" : "Suspicious Signals"}
          </p>

          <p className="text-[10px] text-zinc-500">Authentication evidence</p>
        </div>
      </div>

      <div>
        <StatusRow label="SPF" value={authentication.spf} />

        <StatusRow label="DKIM" value={authentication.dkim} />

        <StatusRow label="DMARC" value={authentication.dmarc} />
      </div>
    </div>
  );
}
