import { useState } from "react";
import DownloadIcon from "@mui/icons-material/Download";
import {
  Box,
  Chip,
  Dialog,
  DialogContent,
  IconButton,
  ImageList,
  ImageListItem,
  ImageListItemBar,
} from "@mui/material";
import { resolveUploadUrl } from "../app/config";
import type { VehiclePhoto } from "../types/api";

export function PhotoGallery({ photos }: { photos: VehiclePhoto[] }) {
  const [preview, setPreview] = useState<VehiclePhoto | null>(null);

  if (photos.length === 0) {
    return null;
  }

  return (
    <>
      <ImageList cols={3} gap={12}>
        {photos.map((photo) => (
          <ImageListItem key={photo.id}>
            <Box
              component="img"
              src={resolveUploadUrl(photo.file_path)}
              alt={photo.photo_type}
              sx={{ height: 160, objectFit: "cover", cursor: "pointer", borderRadius: 1 }}
              onClick={() => setPreview(photo)}
            />
            <ImageListItemBar
              title={photo.file_name ?? photo.photo_type}
              subtitle={photo.photo_type}
              actionIcon={
                <IconButton
                  href={resolveUploadUrl(photo.file_path)}
                  download
                  sx={{ color: "white" }}
                >
                  <DownloadIcon />
                </IconButton>
              }
            />
          </ImageListItem>
        ))}
      </ImageList>
      <Dialog open={Boolean(preview)} onClose={() => setPreview(null)} maxWidth="lg">
        <DialogContent sx={{ position: "relative" }}>
          {preview ? (
            <>
              <Chip label={preview.photo_type} sx={{ mb: 2 }} />
              <Box
                component="img"
                src={resolveUploadUrl(preview.file_path)}
                alt={preview.photo_type}
                sx={{ width: "100%", maxHeight: "80vh", objectFit: "contain" }}
              />
            </>
          ) : null}
        </DialogContent>
      </Dialog>
    </>
  );
}
