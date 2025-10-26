"use server";

import { revalidatePath } from "next/cache";
import { createLibrary as createLibraryAPI, deleteLibrary as deleteLibraryAPI } from "@/lib/api-client";
import type { Library } from "@/lib/api-client";

export async function createLibrary(
  name: string
): Promise<{ success: true; library: Library } | { success: false; error: string }> {
  try {
    const library = await createLibraryAPI(name);
    revalidatePath("/libraries");
    return { success: true, library };
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : "Failed to create library",
    };
  }
}

export async function deleteLibrary(
  id: string
): Promise<{ success: true } | { success: false; error: string }> {
  try {
    await deleteLibraryAPI(id);
    revalidatePath("/libraries");
    return { success: true };
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : "Failed to delete library",
    };
  }
}
