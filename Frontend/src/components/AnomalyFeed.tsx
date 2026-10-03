import {
  useCallback,
  useEffect,
  useState,
} from "react";

import {
  acknowledgeAnomaly,
  getAnomalies,
  type Anomaly,
} from "../api/anomalies";


type AnomalyFeedProps = {
  compact?: boolean;
  limit?: number;
};

export default function AnomalyFeed({
  compact = false,
  limit = 100,
}: AnomalyFeedProps) {

  const [anomalies, setAnomalies] =
    useState<Anomaly[]>([]);

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState<string | null>(null);


  const load = useCallback(
    async () => {

      try {

        const data =
          await getAnomalies(limit);

        setAnomalies(data);
        setError(null);

      } catch (err) {

        setError(
          err instanceof Error
            ? err.message
            : "Unable to load anomalies",
        );

      } finally {

        setLoading(false);
      }
    },
    [limit],
  );


  useEffect(() => {

    load();

    const timer =
      window.setInterval(
        load,
        3000,
      );

    return () =>
      window.clearInterval(timer);

  }, [load]);


  async function acknowledge(
    anomalyId: string,
  ) {

    try {

      const updated =
        await acknowledgeAnomaly(
          anomalyId,
        );

      setAnomalies((current) =>
        current.map((item) =>
          item.anomaly_id === anomalyId
            ? updated
            : item,
        ),
      );

    } catch (err) {

      console.error(
        "Failed to acknowledge anomaly",
        err,
      );
    }
  }


  if (loading) {
    return (
      <div>
        Loading anomaly feed...
      </div>
    );
  }


  if (error) {
    return (
      <div>
        <strong>
          KAVRON backend error
        </strong>

        <div>{error}</div>
      </div>
    );
  }


  return (
    <section
      style={{
        padding: compact ? 12 : 20,
        borderRadius: compact ? 14 : 18,
        background: "#111827",
        color: "white",
      }}
    >

      <div
        style={{
          display: "flex",
          justifyContent:
            "space-between",
          alignItems: "center",
          marginBottom: 16,
        }}
      >

        <div>
          <h2
            style={{
              margin: 0,
              fontSize: compact ? 15 : 20,
            }}
          >
            Anomaly Detection
          </h2>

          <div
            style={{
              opacity: 0.6,
              fontSize: compact ? 11 : 13,
              marginTop: 4,
            }}
          >
            Live intrusion intelligence
          </div>
        </div>

        <div
          style={{
            padding:
              "6px 10px",
            borderRadius: 999,
            background:
              "#dc2626",
            fontSize: 12,
            fontWeight: 700,
          }}
        >
          {anomalies.length} EVENTS
        </div>

      </div>


      {anomalies.length === 0 ? (

        <div
          style={{
            padding: 30,
            textAlign: "center",
            opacity: 0.65,
          }}
        >
          No intrusion anomalies detected.
        </div>

      ) : (

        <div
          style={{
            display: "grid",
            gap: 10,
          }}
        >

          {anomalies.map((item) => (

            <div
              key={item.anomaly_id}
              style={{
                display: "flex",
                justifyContent:
                  "space-between",
                gap: 16,
                padding: 14,
                borderRadius: 14,
                background:
                  item.acknowledged
                    ? "#1f2937"
                    : "#3f1d1d",
                border:
                  "1px solid rgba(255,255,255,0.08)",
              }}
            >

              <div>

                <div
                  style={{
                    fontWeight: 700,
                  }}
                >
                  🚨 {item.message}
                </div>

                <div
                  style={{
                    marginTop: 6,
                    opacity: 0.7,
                    fontSize: 13,
                  }}
                >
                  Camera:{" "}
                  {item.camera_id}
                  {" • "}
                  Track:{" "}
                  {item.track_id ?? "N/A"}
                  {" • "}
                  Confidence:{" "}
                  {(
                    item.confidence * 100
                  ).toFixed(1)}
                  %
                </div>

                <div
                  style={{
                    marginTop: 4,
                    opacity: 0.55,
                    fontSize: 12,
                  }}
                >
                  {item.created_at
                    ? new Date(
                        item.created_at,
                      ).toLocaleString()
                    : ""}
                </div>

              </div>


              <div
                style={{
                  display: "flex",
                  flexDirection:
                    "column",
                  alignItems: "flex-end",
                  gap: 8,
                }}
              >

                <span
                  style={{
                    padding:
                      "5px 9px",
                    borderRadius: 999,
                    background:
                      "#dc2626",
                    fontSize: 11,
                    fontWeight: 800,
                  }}
                >
                  {item.severity}
                </span>


                {!item.acknowledged && (

                  <button
                    onClick={() =>
                      acknowledge(
                        item.anomaly_id,
                      )
                    }
                    style={{
                      border: 0,
                      borderRadius: 8,
                      padding:
                        "7px 10px",
                      cursor: "pointer",
                    }}
                  >
                    Acknowledge
                  </button>

                )}

              </div>

            </div>

          ))}

        </div>
      )}

    </section>
  );
}