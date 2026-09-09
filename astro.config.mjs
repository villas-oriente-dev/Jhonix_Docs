import { defineConfig } from "astro/config";
import starlight from "@astrojs/starlight";

export default defineConfig({
	integrations: [
		starlight({
			title: "JHONIX Apps",
			locales: {
				root: {
					label: "Español",
					lang: "es"
				},
				en: {
					label: "English",
					lang: "en"
				}
			},
			social: [
				{
					icon: "github",
					label: "GitHub",
					href: "https://github.com/villas-oriente-dev"
				}
			],
			sidebar: [
				{
					label: "Inicio",
					translations: { en: "Home" },
					link: "/"
				},
				{
					label: "Apps",
					items: [
						{
							label: "Informes de Predicación",
							items: [
								{ label: "Documentación", link: "/apps/informes-de-predicacion/" },
								{ label: "Política de Privacidad", link: "/apps/informes-de-predicacion/privacidad/" }
							]
						},
						{
							label: "Villas Oriente",
							items: [
								{ label: "Documentación", link: "/apps/villas-oriente/" },
								{ label: "Política de Privacidad", link: "/apps/villas-oriente/privacidad/" }
							]
						},
						{
							label: "Territorios",
							items: [
								{ label: "Documentación", link: "/apps/territorios/" },
								{ label: "Política de Privacidad", link: "/apps/territorios/privacidad/" }
							]
						}
					]
				},
				{
					label: "Diseño y Servicios",
					translations: { en: "Design & Services" },
					link: "/diseno-servicios/"
				}
			],
			customCss: ["./src/styles/custom.css"]
		})
	]
});
