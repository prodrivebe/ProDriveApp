import { useState } from "react";
import { useNavigate } from "react-router-dom";
import SearchIcon from "@mui/icons-material/Search";
import {
  Autocomplete,
  CircularProgress,
  InputAdornment,
  TextField,
} from "@mui/material";
import { useQuery } from "@tanstack/react-query";
import { dashboardService } from "../services/documentsService";
import type { SearchResultItem } from "../types/api";

export function GlobalSearch() {
  const navigate = useNavigate();
  const [query, setQuery] = useState("");

  const searchQuery = useQuery({
    queryKey: ["search", query],
    queryFn: () => dashboardService.search(query),
    enabled: query.trim().length >= 2,
  });

  const options: SearchResultItem[] = searchQuery.data
    ? [
        ...searchQuery.data.orders,
        ...searchQuery.data.customers,
        ...searchQuery.data.drivers,
        ...searchQuery.data.vehicles,
      ]
    : [];

  return (
    <Autocomplete
      sx={{ flex: 1, maxWidth: 520 }}
      options={options}
      loading={searchQuery.isFetching}
      getOptionLabel={(option) => option.title}
      filterOptions={(x) => x}
      onInputChange={(_, value) => setQuery(value)}
      onChange={(_, value) => {
        if (!value) return;
        if (value.type === "order") navigate(`/orders/${value.id}`);
        else if (value.type === "customer") navigate(`/customers/${value.id}`);
        else if (value.type === "driver") navigate(`/drivers/${value.id}`);
        else if (value.type === "vehicle") navigate(`/orders?search=${encodeURIComponent(value.title)}`);
      }}
      renderInput={(params) => (
        <TextField
          {...params}
          placeholder="Search orders, customers, drivers, VIN..."
          size="small"
          InputProps={{
            ...params.InputProps,
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon fontSize="small" />
              </InputAdornment>
            ),
            endAdornment: (
              <>
                {searchQuery.isFetching ? <CircularProgress size={16} /> : null}
                {params.InputProps.endAdornment}
              </>
            ),
          }}
        />
      )}
    />
  );
}
