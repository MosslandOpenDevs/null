import { getRequestConfig } from "next-intl/server";

export default getRequestConfig(async ({ requestLocale }) => {
  const locale = (await requestLocale) || "en";
  return {
    locale,
    messages: (await import(`@/i18n/${locale}.json`)).default,
  };
});
