"use client";

import * as Select from "@radix-ui/react-select";

type Props = {
  label: "Calendar" | "View";
  value: string;
  onValueChange: (value: string) => void;
  options: { value: string; label: string }[];
};

export function CalendarSelect({ label, value, onValueChange, options }: Props) {
  if (options.length < 2) return null;
  return <Select.Root value={value} onValueChange={onValueChange}>
    <Select.Trigger className="calendar-select" aria-label={label} title={label}>
      <svg aria-hidden="true" viewBox="0 0 24 24">{label === "Calendar" ? <><rect x="3" y="5" width="18" height="16" rx="3" /><path d="M7 3v4M17 3v4M3 11h18M7 15h2M13 15h2" /></> : <><path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12Z" /><circle cx="12" cy="12" r="3" /></>}</svg>
      <Select.Value />
      <Select.Icon className="calendar-select-chevron"><svg aria-hidden="true" viewBox="0 0 24 24"><path d="m7 10 5 5 5-5" /></svg></Select.Icon>
    </Select.Trigger>
    <Select.Portal>
      <Select.Content className="calendar-select-menu" position="popper" sideOffset={8} collisionPadding={12}>
        <Select.ScrollUpButton className="calendar-select-scroll" aria-label="Scroll options up">↑</Select.ScrollUpButton>
        <Select.Viewport className="calendar-select-options">
          {options.map(option => <Select.Item className="calendar-select-option" key={option.value} value={option.value}>
            <Select.ItemText>{option.label}</Select.ItemText>
            <Select.ItemIndicator className="calendar-select-check"><svg aria-hidden="true" viewBox="0 0 24 24"><path d="m5 12 4 4L19 6" /></svg></Select.ItemIndicator>
          </Select.Item>)}
        </Select.Viewport>
        <Select.ScrollDownButton className="calendar-select-scroll" aria-label="Scroll options down">↓</Select.ScrollDownButton>
      </Select.Content>
    </Select.Portal>
  </Select.Root>;
}
