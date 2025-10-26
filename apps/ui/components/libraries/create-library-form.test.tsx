import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { CreateLibraryForm } from "./create-library-form";

describe("CreateLibraryForm", () => {
  it("renders the form with correct elements", () => {
    render(<CreateLibraryForm />);

    expect(screen.getByText("Create Your First Library")).toBeInTheDocument();
    expect(screen.getByLabelText("Library Name")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /create library/i })).toBeInTheDocument();
  });

  it("disables submit button when name is empty", () => {
    render(<CreateLibraryForm />);

    const submitButton = screen.getByRole("button", { name: /create library/i });
    expect(submitButton).toBeDisabled();
  });
});
