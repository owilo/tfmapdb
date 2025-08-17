import React from "react";
import { useTranslation } from "react-i18next";
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
} from "./components/ui/dropdown-menu";
import { Check, ChevronDown } from "lucide-react";
import ReactCountryFlag from "react-country-flag";

const LANGUAGES = [
  { code: "en", countryCode: "GB", label: "English" },
  { code: "fr", countryCode: "FR", label: "Français" },
];

export default function LanguageSelector() {
  const { i18n } = useTranslation();

  // Normalize to primary tag if i18n.language is "en-US", etc.
  const currentCode = (i18n.language || "en").split("-")[0];
  const current = LANGUAGES.find((l) => l.code === currentCode) || LANGUAGES[0];

  async function handleChange(code) {
    if (code === currentCode) return;
    try {
      await i18n.changeLanguage(code);
    } catch (err) {
      console.error("Failed to change language", err);
    }
  }

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <button
          aria-label="Change language"
          className="flex items-center gap-2 focus:outline-hidden"
        >
          <ReactCountryFlag
            countryCode={current.countryCode}
            svg
            title={current.label}
            aria-hidden
            className="rounded-sm inline-block align-middle"
          />

          <span className="hidden sm:inline text-sm align-middle leading-none">
            {current.label}
          </span>

          <ChevronDown className="ml-1 h-4 w-4 align-middle" />
        </button>
      </DropdownMenuTrigger>

      <DropdownMenuContent align="start" sideOffset={8} className="w-44 p-1">
        {LANGUAGES.map((lang) => (
          <DropdownMenuItem
            key={lang.code}
            onClick={() => handleChange(lang.code)}
            className="flex items-center justify-between"
            aria-checked={currentCode === lang.code}
            role="menuitemradio"
          >
            <div className="flex items-center gap-3">
              <ReactCountryFlag
                countryCode={lang.countryCode}
                svg
                title={lang.label}
                aria-hidden
                className="rounded-sm inline-block align-middle"
              />
              <span className="text-sm align-middle leading-none">
                {lang.label}
              </span>
            </div>

            {currentCode === lang.code ? (
              <Check className="h-4 w-4 self-center" />
            ) : null}
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}