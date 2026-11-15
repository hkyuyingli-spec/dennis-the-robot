export const SHOW_DRAFTS = true;

export function isHerbalKitchenRecordVisible(status: string): boolean {
  return status === "published" || (SHOW_DRAFTS && status === "draft");
}
