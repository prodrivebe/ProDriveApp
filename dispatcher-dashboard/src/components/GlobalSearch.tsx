import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Autocomplete,
  Box,
  CircularProgress,
  TextField,
} from "@mui/material";
import { apiGet } from "../services/apiClient";
import type { SearchResponse, SearchResultItem } from "../types/api";

export function GlobalSearch() {
  const navigate = useNavigate();
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [options, setOptions] = useState<SearchResultItem[]>([]);

  useEffect(() => {
    if (query.trim().length < 2) {
      setOptions([]);
      return;
    }

    const timer = window.setTimeout(async () => {
      setLoading(true);
      try {
        const results = await apiGet<SearchResponse>(
          `/search?q=${encodeURIComponent(query.trim())}`,
        );
        setOptions([
          ...results.orders,
          ...results.customers,
          ...results.drivers,
          ...results.vehicles,
        ]);
      } catch {
        setOptions([]);
      } finally {
        setLoading(false);
      }
    }, 300);

    return () => window.clearTimeout(timer);
  }, [query]);

  return (
    <Autocomplete
      freeSolo
      options={options}
      loading={loading}
      getOptionLabel={(option) =>
        typeof option === "string" ? option : `${option.title} (${option.type})`
      }
      onInputChange={(_, value) => setQuery(value)}
      onChange={(_, value) => {
        if (!value || typeof value === "string") {
          return;
        }
        if (value.type === "order") {
          navigate(`/orders/${value.id}`);
        } else if (value.type === "customer") {
          navigate("/customers");
        } else if (value.type === "driver") {
          navigate("/fleet");
        } else {
          navigate("/orders");
        }
      }}
      renderInput={(params) => (
        <TextField
          {...params}
          placeholder="Search orders, VIN, drivers, customers..."
          size="small"
          InputProps={{
            ...params.InputProps,
            endAdornment: (
              <>
                {loading ? <CircularProgress color="inherit" size={18} /> : null}
                {params.InputProps.endAdornment}
              </>
            ),
          }}
        />
      )}
      sx={{ minWidth: 320, flex: 1, maxWidth: 560 }}
    />
  );
}
