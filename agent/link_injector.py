"""
Affiliate Link Injector
=======================
Automatically converts product mentions into real Amazon affiliate links.
"""

import re
from typing import Dict, List


class LinkInjector:
    """Injects real Amazon affiliate links into article content."""

    def __init__(self, config: dict):
        self.config = config
        self.affiliate_tag = config.get('affiliate', {}).get('amazon_associate_tag', '')

        # Common product patterns to convert to search links
        self.product_patterns = [
            r'\*\*([^*]+(?:Monitor|Chair|Desk|Keyboard|Mouse|Lamp|Stand|Mat|Webcam|Headset|Speaker)[^*]*)\*\*',
            r'###\s*\d*\.?\s*\*?\*?([^#\n]+(?:Monitor|Chair|Desk|Keyboard|Mouse|Lamp|Stand|Mat|Webcam|Headset|Speaker)[^#\n]*)\*?\*?',
        ]

        # CTA patterns to convert
        self.cta_patterns = [
            (r'[Cc]heck (?:the )?(?:current )?price on Amazon!?\*?\*?', self._make_search_link),
            (r'[Cc]heck (?:it )?out on Amazon!?\*?\*?', self._make_search_link),
            (r'[Ss]ee (?:the )?(?:current )?price on Amazon!?\*?\*?', self._make_search_link),
            (r'[Vv]iew on Amazon!?\*?\*?', self._make_search_link),
            (r'[Bb]uy on Amazon!?\*?\*?', self._make_search_link),
        ]

    def _make_amazon_search_url(self, product_name: str) -> str:
        """Create Amazon search URL with affiliate tag."""
        # Clean product name for search
        search_term = re.sub(r'[^\w\s-]', '', product_name)
        search_term = search_term.strip().replace(' ', '+')

        base_url = "https://www.amazon.com/s"
        return f"{base_url}?k={search_term}&tag={self.affiliate_tag}"

    def _make_search_link(self, product_context: str) -> str:
        """Create a markdown link for Amazon search."""
        url = self._make_amazon_search_url(product_context)
        return f"[Check price on Amazon]({url})"

    def inject_links(self, content: str, keyword: str) -> str:
        """
        Process article content and inject affiliate links.
        """
        if not self.affiliate_tag:
            return content

        lines = content.split('\n')
        processed_lines = []
        current_product = keyword  # Default context

        for line in lines:
            # Track current product context from headers
            header_match = re.search(r'###?\s*\d*\.?\s*\*?\*?([^#\n*]+)', line)
            if header_match:
                potential_product = header_match.group(1).strip()
                if len(potential_product) > 5:
                    current_product = potential_product

            # Replace CTA patterns with actual links
            modified_line = line
            for pattern, link_maker in self.cta_patterns:
                if re.search(pattern, modified_line):
                    link = link_maker(current_product)
                    modified_line = re.sub(pattern, link, modified_line)

            processed_lines.append(modified_line)

        return '\n'.join(processed_lines)

    def add_product_links(self, content: str) -> str:
        """Add Amazon links to specific product mentions."""
        if not self.affiliate_tag:
            return content

        # Find product names in bold and add links if not already linked
        def replace_product(match):
            product_name = match.group(1)
            # Skip if already in a link
            if '](' in product_name or product_name.startswith('['):
                return match.group(0)

            url = self._make_amazon_search_url(product_name)
            return f"**[{product_name}]({url})**"

        # Only link first occurrence of each product
        seen_products = set()
        lines = content.split('\n')
        result_lines = []

        for line in lines:
            # Don't modify headers
            if line.startswith('#'):
                result_lines.append(line)
                continue

            for pattern in self.product_patterns:
                matches = list(re.finditer(pattern, line))
                for match in matches:
                    product = match.group(1).strip()
                    if product not in seen_products and len(product) > 10:
                        seen_products.add(product)
                        url = self._make_amazon_search_url(product)
                        old_text = match.group(0)
                        new_text = f"**[{product}]({url})**"
                        line = line.replace(old_text, new_text, 1)

            result_lines.append(line)

        return '\n'.join(result_lines)

    def process_article(self, content: str, keyword: str) -> str:
        """Full processing pipeline for an article."""
        # First inject CTA links
        content = self.inject_links(content, keyword)

        # Then add product links
        content = self.add_product_links(content)

        return content
