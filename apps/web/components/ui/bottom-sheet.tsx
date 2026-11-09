"use client";

import { Drawer } from "vaul";
import { cn } from "@/lib/utils";

export const BottomSheet = Drawer.Root;
export const BottomSheetTrigger = Drawer.Trigger;
export const BottomSheetClose = Drawer.Close;

export function BottomSheetContent({
  className,
  children,
}: {
  className?: string;
  children: React.ReactNode;
}) {
  return (
    <Drawer.Portal>
      <Drawer.Overlay className="fixed inset-0 z-50 bg-[#0c2410]/45" />
      <Drawer.Content
        className={cn(
          "safe-bottom fixed right-0 bottom-0 left-0 z-50 max-h-[88vh] rounded-t-[28px] border-t border-line bg-canvas px-5 pt-3 shadow-2xl",
          className,
        )}
      >
        <div className="mx-auto mb-5 h-1.5 w-11 rounded-full bg-[#c9d5ca]" />
        {children}
      </Drawer.Content>
    </Drawer.Portal>
  );
}

export const BottomSheetTitle = Drawer.Title;
export const BottomSheetDescription = Drawer.Description;
