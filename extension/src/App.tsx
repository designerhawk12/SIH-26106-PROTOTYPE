import { useEffect, useState } from "react";

import {
  fetchEmails,
  scanEmail,
  type EmailSummary,
  type ScanResult,
} from "./hooks/useApi";

import Shield from "./components/Shield";
import Map from "./components/Map";
import HopSequence from "./components/HopSequence";

type View = "list" | "scanning" | "result";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

function App() {
  const [view, setView] = useState<View>("list");

  const [emails, setEmails] = useState<EmailSummary[]>([]);

  const [nextPageToken, setNextPageToken] = useState<string | null>(null);

  const [selectedEmail, setSelectedEmail] = useState<EmailSummary | null>(null);

  const [result, setResult] = useState<ScanResult | null>(null);

  const [selectedHopIndex, setSelectedHopIndex] = useState<number | null>(null);

  const [loading, setLoading] = useState(true);

  const [loadingMore, setLoadingMore] = useState(false);

  const [error, setError] = useState<string | null>(null);

  const [authenticated, setAuthenticated] = useState(false);

  const [authChecking, setAuthChecking] = useState(true);

  const [connecting, setConnecting] = useState(false);

  // -----------------------------------------------------
  // Authentication + Initial load
  // -----------------------------------------------------

  useEffect(() => {
    initialize();
  }, []);

  async function checkAuthentication(): Promise<boolean> {
    try {
      setAuthChecking(true);
      setError(null);

      const response = await fetch(`${API_BASE}/api/v1/extension/auth/status`);

      if (!response.ok) {
        throw new Error(`Authentication check failed (${response.status})`);
      }

      const data = await response.json();

      const isAuthenticated = data?.authenticated === true;

      setAuthenticated(isAuthenticated);

      return isAuthenticated;
    } catch (err) {
      setAuthenticated(false);
      setError(
        err instanceof Error
          ? err.message
          : "Unable to check Gmail authentication",
      );

      return false;
    } finally {
      setAuthChecking(false);
    }
  }

  async function initialize() {
    try {
      setLoading(true);
      setError(null);

      const isAuthenticated = await checkAuthentication();

      if (!isAuthenticated) {
        return;
      }

      await loadEmails();
    } finally {
      setLoading(false);
    }
  }

  async function loadEmails() {
    try {
      setError(null);

      const page = await fetchEmails(10);

      setEmails(page.emails);

      setNextPageToken(page.next_page_token);
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Failed to load emails";

      setError(message);

      if (message.includes("(401)")) {
        setAuthenticated(false);
      }
    }
  }

  // -----------------------------------------------------
  // Gmail authentication
  // -----------------------------------------------------

  function startGmailAuthentication() {
    setError(null);
    setConnecting(true);

    const loginUrl = `${API_BASE}/api/v1/extension/auth/login`;

    window.open(loginUrl, "_blank", "noopener,noreferrer");

    pollAuthentication();
  }

  async function pollAuthentication() {
    const maxAttempts = 180;

    for (let attempt = 0; attempt < maxAttempts; attempt += 1) {
      await new Promise((resolve) => {
        window.setTimeout(resolve, 1000);
      });

      try {
        const response = await fetch(
          `${API_BASE}/api/v1/extension/auth/status`,
          {
            cache: "no-store",
          },
        );

        if (!response.ok) {
          continue;
        }

        const data = await response.json();

        if (data?.authenticated === true) {
          setAuthenticated(true);
          setConnecting(false);
          setLoading(true);
          setError(null);

          try {
            await loadEmails();
          } finally {
            setLoading(false);
          }

          return;
        }
      } catch {
        // Keep polling while the OAuth flow is in progress.
      }
    }

    setConnecting(false);

    const authenticatedNow = await checkAuthentication();

    if (!authenticatedNow) {
      setError(
        "Gmail authorization was not completed. Please try connecting again.",
      );
    }
  }

  async function handleRefresh() {
    setError(null);
    setLoading(true);

    try {
      const isAuthenticated = await checkAuthentication();

      if (!isAuthenticated) {
        return;
      }

      await loadEmails();
    } finally {
      setLoading(false);
    }
  }

  // -----------------------------------------------------
  // Load more
  // -----------------------------------------------------

  async function loadMoreEmails() {
    if (!nextPageToken || loadingMore || !authenticated) {
      return;
    }

    try {
      setLoadingMore(true);
      setError(null);

      const page = await fetchEmails(10, nextPageToken);

      setEmails((current) => [...current, ...page.emails]);

      setNextPageToken(page.next_page_token);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to load more emails",
      );
    } finally {
      setLoadingMore(false);
    }
  }

  // -----------------------------------------------------
  // Select + scan
  // -----------------------------------------------------

  async function handleSelectEmail(email: EmailSummary) {
    console.log("[Email Shield] Email clicked:", email.id);

    setSelectedEmail(email);

    setResult(null);

    setSelectedHopIndex(null);

    setError(null);

    setView("scanning");

    try {
      const scan = await scanEmail(email.id);

      console.log("[Email Shield] Scan complete:", scan);

      setResult(scan);

      setView("result");
    } catch (err) {
      console.error("[Email Shield] Scan failed:", err);

      const message = err instanceof Error ? err.message : "Email scan failed";

      setError(message);

      if (message.includes("(401)")) {
        setAuthenticated(false);
      }

      setView("list");
    }
  }

  // -----------------------------------------------------
  // Back
  // -----------------------------------------------------

  function handleBack() {
    setResult(null);

    setSelectedEmail(null);

    setSelectedHopIndex(null);

    setError(null);

    setView("list");
  }

  // =====================================================
  // LIST
  // =====================================================

  if (view === "list") {
    return (
      <div
        className="
          w-[420px]
          min-h-[420px]
          bg-zinc-950
          text-zinc-100
        "
      >
        {/* Header */}

        <div
          className="
            border-b
            border-zinc-800
            px-4
            py-4
          "
        >
          <div
            className="
              flex
              items-center
              justify-between
            "
          >
            <div>
              <h1
                className="
                  text-xl
                  font-bold
                "
              >
                Email Shield
              </h1>

              <div className="mt-1 flex items-center gap-2">
                <p
                  className="
                    text-[10px]
                    uppercase
                    tracking-[0.18em]
                    text-zinc-600
                  "
                >
                  SIH26106 • Email Forensics
                </p>

                <span className="text-zinc-800">•</span>

                <a
                  href="http://localhost:3000"
                  target="_blank"
                  rel="noreferrer"
                  className="
                    text-[10px]
                    text-emerald-500/70
                    transition
                    hover:text-emerald-400
                  "
                >
                  Open Dashboard ↗
                </a>
              </div>
            </div>

            <button
              type="button"
              onClick={handleRefresh}
              disabled={loading || authChecking || connecting}
              className="
                rounded-md
                border
                border-zinc-800
                bg-zinc-900
                px-3
                py-1.5
                text-xs
                text-zinc-400
                hover:bg-zinc-800
                disabled:opacity-40
              "
            >
              {loading || authChecking ? "Loading..." : "Refresh"}
            </button>
          </div>
        </div>

        {/* Content */}

        <div className="p-4">
          {/* Authentication check */}

          {authChecking && (
            <div
              className="
                flex
                min-h-[250px]
                flex-col
                items-center
                justify-center
              "
            >
              <div
                className="
                  mb-4
                  h-8
                  w-8
                  animate-spin
                  rounded-full
                  border-2
                  border-zinc-700
                  border-t-emerald-400
                "
              />

              <p
                className="
                  text-sm
                  text-zinc-500
                "
              >
                Checking Gmail...
              </p>
            </div>
          )}

          {/* Gmail authentication required */}

          {!authChecking && !authenticated && !connecting && (
            <div
              className="
                flex
                min-h-[250px]
                flex-col
                items-center
                justify-center
                px-4
                text-center
              "
            >
              <div
                className="
                  mb-5
                  flex
                  h-16
                  w-16
                  items-center
                  justify-center
                  rounded-full
                  border
                  border-emerald-500/20
                  bg-emerald-500/5
                "
              >
                <div
                  className="
                    h-7
                    w-7
                    rounded-md
                    border-2
                    border-emerald-400/70
                  "
                />
              </div>

              <p
                className="
                  text-base
                  font-semibold
                  text-zinc-200
                "
              >
                Connect Gmail
              </p>

              <p
                className="
                  mt-2
                  max-w-[300px]
                  text-xs
                  leading-relaxed
                  text-zinc-500
                "
              >
                Sign in with the configured developer Gmail account to load
                messages for forensic analysis.
              </p>

              <button
                type="button"
                onClick={startGmailAuthentication}
                className="
                  mt-6
                  rounded-md
                  border
                  border-emerald-500/30
                  bg-emerald-500/10
                  px-4
                  py-2
                  text-xs
                  font-medium
                  text-emerald-400
                  transition
                  hover:bg-emerald-500/20
                  hover:text-emerald-300
                "
              >
                Connect Gmail
              </button>

              {error && (
                <p
                  className="
                    mt-4
                    max-w-[300px]
                    text-[10px]
                    leading-relaxed
                    text-red-500/70
                  "
                >
                  {error}
                </p>
              )}
            </div>
          )}

          {/* Connecting */}

          {!authChecking && connecting && (
            <div
              className="
                flex
                min-h-[250px]
                flex-col
                items-center
                justify-center
                px-4
                text-center
              "
            >
              <div
                className="
                  relative
                  mb-6
                  flex
                  h-16
                  w-16
                  items-center
                  justify-center
                  rounded-full
                  border
                  border-emerald-500/20
                  bg-emerald-500/5
                "
              >
                <div
                  className="
                    absolute
                    inset-1
                    animate-ping
                    rounded-full
                    border
                    border-emerald-400/10
                  "
                />

                <div
                  className="
                    h-7
                    w-7
                    animate-spin
                    rounded-full
                    border-2
                    border-zinc-800
                    border-t-emerald-400
                  "
                />
              </div>

              <p
                className="
                  text-base
                  font-semibold
                  text-zinc-200
                "
              >
                Waiting for Gmail
              </p>

              <p
                className="
                  mt-2
                  max-w-[300px]
                  text-xs
                  leading-relaxed
                  text-zinc-500
                "
              >
                Complete the Google sign-in in the browser tab that was opened.
              </p>

              <p
                className="
                  mt-4
                  text-[9px]
                  uppercase
                  tracking-[0.2em]
                  text-emerald-500/60
                "
              >
                OAuth • Gmail Readonly
              </p>
            </div>
          )}

          {/* Loading Gmail */}

          {!authChecking && authenticated && loading && (
            <div
              className="
                  flex
                  min-h-[250px]
                  flex-col
                  items-center
                  justify-center
                "
            >
              <div
                className="
                    mb-4
                    h-8
                    w-8
                    animate-spin
                    rounded-full
                    border-2
                    border-zinc-700
                    border-t-emerald-400
                  "
              />

              <p
                className="
                    text-sm
                    text-zinc-500
                  "
              >
                Loading Gmail...
              </p>
            </div>
          )}

          {/* Error */}

          {!authChecking && authenticated && !loading && error && (
            <div
              className="
                  rounded-lg
                  border
                  border-red-900/60
                  bg-red-950/30
                  p-4
                "
            >
              <p
                className="
                    text-sm
                    font-semibold
                    text-red-400
                  "
              >
                Error
              </p>

              <p
                className="
                    mt-1
                    break-words
                    text-xs
                    text-red-500/70
                  "
              >
                {error}
              </p>
            </div>
          )}

          {/* Empty */}

          {!authChecking &&
            authenticated &&
            !loading &&
            !error &&
            emails.length === 0 && (
              <div
                className="
                  py-12
                  text-center
                  text-sm
                  text-zinc-600
                "
              >
                No emails found.
              </div>
            )}

          {/* Email list */}

          {!authChecking &&
            authenticated &&
            !loading &&
            !error &&
            emails.length > 0 && (
              <div className="space-y-2">
                {emails.map((email) => (
                  <button
                    key={email.id}
                    type="button"
                    onClick={() => handleSelectEmail(email)}
                    className="
                      group
                      w-full
                      rounded-lg
                      border
                      border-zinc-800
                      bg-zinc-900
                      p-3
                      text-left
                      transition
                      hover:border-zinc-700
                      hover:bg-zinc-800
                      active:scale-[0.99]
                      focus:outline-none
                      focus:ring-1
                      focus:ring-emerald-500/50
                    "
                  >
                    <div
                      className="
                        truncate
                        text-sm
                        font-semibold
                        text-zinc-100
                      "
                    >
                      {email.subject || "No Subject"}
                    </div>

                    <div
                      className="
                        mt-1
                        truncate
                        text-xs
                        text-zinc-400
                      "
                    >
                      {email.sender}
                    </div>

                    {email.date && (
                      <div
                        className="
                          mt-2
                          text-[10px]
                          text-zinc-600
                        "
                      >
                        {email.date}
                      </div>
                    )}
                  </button>
                ))}
              </div>
            )}

          {/* Load more */}

          {!authChecking &&
            authenticated &&
            !loading &&
            !error &&
            nextPageToken && (
              <button
                type="button"
                onClick={loadMoreEmails}
                disabled={loadingMore}
                className="
                  mt-4
                  w-full
                  rounded-lg
                  border
                  border-zinc-800
                  bg-zinc-900
                  py-2.5
                  text-xs
                  font-medium
                  text-zinc-400
                  transition
                  hover:bg-zinc-800
                  hover:text-zinc-200
                  disabled:opacity-40
                "
              >
                {loadingMore ? "Loading more..." : "Load More Emails"}
              </button>
            )}
        </div>
      </div>
    );
  }

  // =====================================================
  // SCANNING
  // =====================================================

  if (view === "scanning") {
    return (
      <div
        className="
          flex
          min-h-[420px]
          w-[420px]
          flex-col
          items-center
          justify-center
          bg-zinc-950
          px-8
          text-zinc-100
        "
      >
        <div
          className="
            relative
            mb-7
            flex
            h-24
            w-24
            items-center
            justify-center
            rounded-full
            border
            border-emerald-500/20
            bg-emerald-500/5
          "
        >
          <div
            className="
              absolute
              inset-2
              animate-ping
              rounded-full
              border
              border-emerald-400/20
            "
          />

          <div
            className="
              h-12
              w-12
              animate-spin
              rounded-full
              border-2
              border-zinc-800
              border-t-emerald-400
            "
          />
        </div>

        <p
          className="
            text-base
            font-semibold
          "
        >
          Analyzing Email
        </p>

        {selectedEmail && (
          <p
            className="
              mt-2
              max-w-[330px]
              truncate
              text-center
              text-xs
              text-zinc-500
            "
          >
            {selectedEmail.subject}
          </p>
        )}

        <div
          className="
            mt-6
            text-[9px]
            uppercase
            tracking-[0.2em]
            text-emerald-500/60
          "
        >
          MIME • HEADERS • AUTH • GEO
        </div>
      </div>
    );
  }

  // =====================================================
  // RESULT
  // =====================================================

  if (view === "result" && result) {
    return (
      <div
        className="
          w-[420px]
          min-h-[500px]
          bg-zinc-950
          text-zinc-100
        "
      >
        <div
          className="
            border-b
            border-zinc-800
            px-4
            py-3
          "
        >
          <button
            type="button"
            onClick={handleBack}
            className="
              text-xs
              text-zinc-500
              hover:text-zinc-200
            "
          >
            ← Back to emails
          </button>

          <div className="mt-3">
            <h2
              className="
                truncate
                text-base
                font-semibold
              "
            >
              {result.email.subject || "Scanned Email"}
            </h2>

            <p
              className="
                mt-1
                truncate
                text-xs
                text-zinc-500
              "
            >
              {result.email.from || "Unknown Sender"}
            </p>
          </div>
        </div>

        <div className="p-4">
          <Shield
            verdict={result.verdict}
            authentication={result.authentication}
          />

          <div className="mt-5">
            <div
              className="
                mb-2
                flex
                items-center
                justify-between
              "
            >
              <h3
                className="
                  text-xs
                  font-semibold
                  uppercase
                  tracking-[0.15em]
                  text-zinc-500
                "
              >
                Origin Atlas
              </h3>

              <span
                className="
                  text-[9px]
                  text-zinc-700
                "
              >
                GEOLOCATION
              </span>
            </div>

            <Map
              hops={result.received_chain}
              selectedHopIndex={selectedHopIndex}
            />
          </div>

          <div className="mt-5">
            <HopSequence
              hops={result.received_chain}
              selectedHopIndex={selectedHopIndex}
              onSelectHop={setSelectedHopIndex}
            />
          </div>

          <div
            className="
              mt-5
              grid
              grid-cols-3
              gap-2
            "
          >
            <div
              className="
                rounded-lg
                border
                border-zinc-800
                bg-zinc-900
                p-2
              "
            >
              <p
                className="
                  text-[9px]
                  uppercase
                  text-zinc-600
                "
              >
                URLs
              </p>

              <p
                className="
                  mt-1
                  text-sm
                  font-semibold
                "
              >
                {result.indicators.urls.length}
              </p>
            </div>

            <div
              className="
                rounded-lg
                border
                border-zinc-800
                bg-zinc-900
                p-2
              "
            >
              <p
                className="
                  text-[9px]
                  uppercase
                  text-zinc-600
                "
              >
                Domains
              </p>

              <p
                className="
                  mt-1
                  text-sm
                  font-semibold
                "
              >
                {result.indicators.domains.length}
              </p>
            </div>

            <div
              className="
                rounded-lg
                border
                border-zinc-800
                bg-zinc-900
                p-2
              "
            >
              <p
                className="
                  text-[9px]
                  uppercase
                  text-zinc-600
                "
              >
                Body IPs
              </p>

              <p
                className="
                  mt-1
                  text-sm
                  font-semibold
                "
              >
                {result.indicators.ips.length}
              </p>
            </div>
          </div>

          {result.parse_warnings.length > 0 && (
            <div
              className="
                mt-4
                rounded-lg
                border
                border-yellow-900/60
                bg-yellow-950/20
                p-3
              "
            >
              <p
                className="
                  text-[10px]
                  font-semibold
                  uppercase
                  text-yellow-500
                "
              >
                Analysis Notes
              </p>

              <p
                className="
                  mt-1
                  text-[10px]
                  leading-relaxed
                  text-yellow-600/80
                "
              >
                {result.parse_warnings.join(" • ")}
              </p>
            </div>
          )}
        </div>
      </div>
    );
  }

  return null;
}

export default App;
