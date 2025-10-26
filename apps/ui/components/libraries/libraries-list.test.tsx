import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { LibrariesList } from "./libraries-list";
import type { Library } from "@/lib/api-client";

// Mock the CreateLibraryForm component
vi.mock("./create-library-form", () => ({
  CreateLibraryForm: () => <div data-testid="create-library-form">Create Form</div>,
}));

describe("LibrariesList", () => {
  it("renders create form when no libraries exist", () => {
    render(<LibrariesList initialLibraries={[]} />);

    expect(screen.getByTestId("create-library-form")).toBeInTheDocument();
  });

  it("renders table when libraries exist", () => {
    const libraries: Library[] = [
      { id: "lib-1", name: "Library One", created_at: "2024-01-01T00:00:00Z", updated_at: "2024-01-01T00:00:00Z" },
      { id: "lib-2", name: "Library Two", created_at: "2024-01-02T00:00:00Z", updated_at: "2024-01-02T00:00:00Z" },
    ];

    render(<LibrariesList initialLibraries={libraries} />);

    expect(screen.getByRole("table")).toBeInTheDocument();
    expect(screen.getByText("Library One")).toBeInTheDocument();
    expect(screen.getByText("Library Two")).toBeInTheDocument();
  });
});
