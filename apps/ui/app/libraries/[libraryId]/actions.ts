"use server";

import { revalidatePath } from "next/cache";
import { uploadDocument as uploadDocumentAPI } from "@/lib/api-client";
import type { Document } from "@/lib/api-client";

export async function uploadDocument(
  libraryId: string,
  formData: FormData
): Promise<{ success: true; document: Document } | { success: false; error: string }> {
  try {
    const file = formData.get("file") as File;
    if (!file) {
      return { success: false, error: "No file provided" };
    }

    const document = await uploadDocumentAPI(libraryId, file);
    revalidatePath(`/libraries/${libraryId}`);
    return { success: true, document };
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : "Failed to upload document",
    };
  }
}
