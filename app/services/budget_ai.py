"""AI-powered budget generation and debt paydown strategy service."""
import statistics
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from decimal import Decimal
from collections import defaultdict

from ..models import NormalizedTransaction
from ..util.logging import logger
from ..deps import get_supabase_client


class BudgetAI:
    """AI-powered budget analysis and debt paydown strategy recommendations."""

    def __init__(self):
        self.supabase = get_supabase_client()

        # Essential vs discretionary spending patterns
        self.ESSENTIAL_CATEGORIES = {
            'council_tax', 'water', 'energy', 'broadband', 'mortgage', 'rent',
            'insurance', 'mobile', 'council', 'groceries', 'transport', 'utilities'
        }

        self.DISCRETIONARY_CATEGORIES = {
            'entertainment', 'dining', 'shopping', 'subscriptions', 'hobbies',
            'travel', 'luxury', 'gifts', 'charity'
        }

    async def analyze_spending_patterns(self, user_id: str, transactions: List[NormalizedTransaction]) -> Dict[str, Any]:
        """
        Analyze spending patterns to suggest budget categories and amounts.

        Returns:
        - Category analysis with suggested amounts
        - Essential vs discretionary breakdown
        - Spending trends and anomalies
        """
        try:
            logger.info(f"Analyzing spending patterns for user {user_id} with {len(transactions)} transactions")

            # Group transactions by category
            category_spending = defaultdict(list)
            uncategorized_spending = []

            for tx in transactions:
                if tx.category:
                    category_spending[tx.category].append(tx)
                else:
                    uncategorized_spending.append(tx)

            # Analyze each category
            category_analysis = {}
            total_spent = Decimal('0')

            for category, txs in category_spending.items():
                amounts = [abs(tx.amount) for tx in txs if tx.amount < 0]  # Only spending
                if not amounts:
                    continue

                avg_spending = statistics.mean(amounts)
                median_spending = statistics.median(amounts)
                max_spending = max(amounts)
                min_spending = min(amounts)
                frequency = len(txs)

                # Calculate suggested budget (median + 20% buffer)
                suggested_budget = Decimal(str(median_spending * 1.2))

                # Determine if essential or discretionary
                is_essential = category in self.ESSENTIAL_CATEGORIES

                category_analysis[category] = {
                    'total_spent': sum(amounts),
                    'average_spending': avg_spending,
                    'median_spending': median_spending,
                    'max_spending': max_spending,
                    'min_spending': min_spending,
                    'frequency': frequency,
                    'suggested_budget': float(suggested_budget),
                    'is_essential': is_essential,
                    'confidence': self._calculate_category_confidence(txs)
                }

                total_spent += sum(amounts)

            # Analyze uncategorized spending
            uncategorized_amounts = [abs(tx.amount) for tx in uncategorized_spending if tx.amount < 0]
            uncategorized_total = sum(uncategorized_amounts) if uncategorized_amounts else Decimal('0')

            # Calculate essential vs discretionary breakdown
            essential_total = Decimal('0')
            discretionary_total = Decimal('0')

            for category, analysis in category_analysis.items():
                if analysis['is_essential']:
                    essential_total += Decimal(str(analysis['total_spent']))
                else:
                    discretionary_total += Decimal(str(analysis['total_spent']))

            # Generate insights
            insights = self._generate_spending_insights(category_analysis, total_spent, essential_total, discretionary_total)

            result = {
                'category_analysis': category_analysis,
                'total_spent': float(total_spent),
                'essential_spending': float(essential_total),
                'discretionary_spending': float(discretionary_total),
                'uncategorized_spending': float(uncategorized_total),
                'insights': insights,
                'suggested_categories': self._suggest_new_categories(uncategorized_spending)
            }

            logger.info(f"Spending analysis complete: {len(category_analysis)} categories analyzed")
            return result

        except Exception as e:
            logger.error(f"Error analyzing spending patterns: {e}", exc_info=True)
            return {}

    def _calculate_category_confidence(self, transactions: List[NormalizedTransaction]) -> float:
        """Calculate confidence score for category analysis."""
        if len(transactions) < 3:
            return 0.5  # Low confidence for few transactions

        # Higher confidence for more transactions and consistent amounts
        amounts = [abs(tx.amount) for tx in transactions]
        if len(amounts) < 2:
            return 0.5

        # Calculate coefficient of variation (lower = more consistent)
        mean_amount = statistics.mean(amounts)
        std_amount = statistics.stdev(amounts) if len(amounts) > 1 else 0
        cv = std_amount / mean_amount if mean_amount > 0 else 1

        # Confidence based on consistency and sample size
        consistency_score = max(0, 1 - cv)  # Lower variation = higher confidence
        sample_size_score = min(1, len(transactions) / 10)  # More transactions = higher confidence

        return (consistency_score * 0.7) + (sample_size_score * 0.3)

    def _generate_spending_insights(self, category_analysis: Dict, total_spent: Decimal,
                                 essential_total: Decimal, discretionary_total: Decimal) -> List[str]:
        """Generate spending insights and recommendations."""
        insights = []

        # Essential vs discretionary ratio
        if total_spent > 0:
            essential_ratio = float(essential_total / total_spent)
            if essential_ratio > 0.8:
                insights.append("Your spending is heavily focused on essentials (80%+). Consider reviewing discretionary spending.")
            elif essential_ratio < 0.5:
                insights.append("High discretionary spending detected. Consider prioritizing essential expenses.")
            else:
                insights.append("Good balance between essential and discretionary spending.")

        # High spending categories
        high_spending_categories = [
            (cat, analysis['total_spent'])
            for cat, analysis in category_analysis.items()
            if analysis['total_spent'] > float(total_spent) * 0.2
        ]

        if high_spending_categories:
            top_category = max(high_spending_categories, key=lambda x: x[1])
            insights.append(f"Highest spending category: {top_category[0]} (£{top_category[1]:.2f})")

        # Irregular spending patterns
        irregular_categories = [
            cat for cat, analysis in category_analysis.items()
            if analysis['confidence'] < 0.6 and analysis['frequency'] > 1
        ]

        if irregular_categories:
            insights.append(f"Irregular spending detected in: {', '.join(irregular_categories)}")

        return insights

    def _suggest_new_categories(self, uncategorized_transactions: List[NormalizedTransaction]) -> List[Dict[str, Any]]:
        """Suggest new categories based on uncategorized transactions."""
        if not uncategorized_transactions:
            return []

        # Group by merchant
        merchant_groups = defaultdict(list)
        for tx in uncategorized_transactions:
            if tx.merchant:
                merchant_groups[tx.merchant].append(tx)

        suggestions = []
        for merchant, txs in merchant_groups.items():
            if len(txs) >= 2:  # Only suggest categories for merchants with multiple transactions
                amounts = [abs(tx.amount) for tx in txs if tx.amount < 0]
                if amounts:
                    avg_amount = statistics.mean(amounts)
                    suggested_category = self._infer_category_from_merchant(merchant)

                    suggestions.append({
                        'merchant': merchant,
                        'transaction_count': len(txs),
                        'average_amount': avg_amount,
                        'suggested_category': suggested_category,
                        'confidence': min(1.0, len(txs) / 5)  # More transactions = higher confidence
                    })

        return suggestions

    def _infer_category_from_merchant(self, merchant: str) -> str:
        """Infer category from merchant name."""
        merchant_lower = merchant.lower()

        # Common merchant patterns
        if any(word in merchant_lower for word in ['tesco', 'sainsbury', 'asda', 'morrisons', 'waitrose', 'coop']):
            return 'groceries'
        elif any(word in merchant_lower for word in ['uber', 'bolt', 'taxi', 'bus', 'train', 'tube']):
            return 'transport'
        elif any(word in merchant_lower for word in ['amazon', 'ebay', 'shop', 'store', 'retail']):
            return 'shopping'
        elif any(word in merchant_lower for word in ['restaurant', 'cafe', 'pub', 'bar', 'food', 'eat']):
            return 'dining'
        elif any(word in merchant_lower for word in ['netflix', 'spotify', 'apple', 'google', 'subscription']):
            return 'subscriptions'
        elif any(word in merchant_lower for word in ['cinema', 'theatre', 'entertainment', 'fun']):
            return 'entertainment'
        else:
            return 'other'

    async def suggest_debt_paydown_strategy(self, user_id: str, debt_accounts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Suggest debt paydown strategy (avalanche vs snowball).

        Returns:
        - Avalanche strategy (highest interest first)
        - Snowball strategy (smallest balance first)
        - Recommendation with projections
        """
        try:
            logger.info(f"Analyzing debt paydown strategies for user {user_id}")

            if not debt_accounts:
                return {
                    'strategy': 'none',
                    'message': 'No debt accounts found',
                    'avalanche': [],
                    'snowball': [],
                    'recommendation': 'none'
                }

            # Calculate avalanche strategy (highest interest first)
            avalanche_order = sorted(
                debt_accounts,
                key=lambda x: x.get('interest_rate', 0),
                reverse=True
            )

            # Calculate snowball strategy (smallest balance first)
            snowball_order = sorted(
                debt_accounts,
                key=lambda x: x.get('current_balance', 0)
            )

            # Calculate projections
            avalanche_projection = self._calculate_paydown_projection(avalanche_order)
            snowball_projection = self._calculate_paydown_projection(snowball_order)

            # Make recommendation
            recommendation = self._choose_strategy(avalanche_projection, snowball_projection)

            result = {
                'strategy': recommendation,
                'avalanche': {
                    'order': avalanche_order,
                    'projection': avalanche_projection
                },
                'snowball': {
                    'order': snowball_order,
                    'projection': snowball_projection
                },
                'recommendation': recommendation,
                'reasoning': self._get_strategy_reasoning(recommendation, avalanche_projection, snowball_projection)
            }

            logger.info(f"Debt strategy analysis complete: {recommendation} recommended")
            return result

        except Exception as e:
            logger.error(f"Error analyzing debt paydown strategies: {e}", exc_info=True)
            return {'strategy': 'error', 'message': str(e)}

    def _calculate_paydown_projection(self, debt_order: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate paydown projection for a given strategy."""
        total_balance = sum(account.get('current_balance', 0) for account in debt_order)
        total_minimum_payments = sum(account.get('minimum_payment', 0) for account in debt_order)

        # Assume extra payment of £200/month (this could be configurable)
        extra_payment = 200
        total_monthly_payment = total_minimum_payments + extra_payment

        # Simple projection (doesn't account for interest changes)
        months_to_payoff = total_balance / total_monthly_payment if total_monthly_payment > 0 else 0

        return {
            'total_balance': total_balance,
            'monthly_payment': total_monthly_payment,
            'months_to_payoff': months_to_payoff,
            'total_interest_saved': 0,  # Would need more complex calculation
            'order': debt_order
        }

    def _choose_strategy(self, avalanche_projection: Dict, snowball_projection: Dict) -> str:
        """Choose between avalanche and snowball strategies."""
        # Simple heuristic: if interest rates vary significantly, choose avalanche
        # Otherwise, choose snowball for psychological benefits

        # This is a simplified decision - in practice, you'd want more sophisticated analysis
        if avalanche_projection['months_to_payoff'] < snowball_projection['months_to_payoff']:
            return 'avalanche'
        else:
            return 'snowball'

    def _get_strategy_reasoning(self, strategy: str, avalanche_projection: Dict, snowball_projection: Dict) -> str:
        """Get reasoning for strategy recommendation."""
        if strategy == 'avalanche':
            return "Avalanche method recommended: Paying highest interest debts first will save more money overall."
        elif strategy == 'snowball':
            return "Snowball method recommended: Paying smallest balances first provides psychological motivation."
        else:
            return "No clear advantage between strategies. Choose based on personal preference."

    async def generate_budget_from_patterns(self, user_id: str, lookback_days: int = 90) -> Dict[str, Any]:
        """
        Generate budget from spending patterns.

        Returns:
        - Suggested budget categories with amounts
        - Debt paydown recommendations
        - Budget templates for future use
        """
        try:
            logger.info(f"Generating budget from patterns for user {user_id}")

            # Get recent transactions from cache
            cache_result = self.supabase.table("transaction_cache").select("*").eq(
                "user_id", user_id
            ).gte("posted_at", (datetime.utcnow() - timedelta(days=lookback_days)).isoformat()).execute()

            if not cache_result.data:
                return {
                    'error': 'No transaction data available',
                    'suggested_categories': [],
                    'debt_recommendations': [],
                    'budget_templates': []
                }

            # Convert to NormalizedTransaction objects
            transactions = []
            for tx_data in cache_result.data:
                tx = NormalizedTransaction(
                    id=tx_data['tx_hash'],
                    posted_at=datetime.fromisoformat(tx_data['posted_at']),
                    amount=Decimal(str(tx_data['amount'])),
                    currency='GBP',
                    description='',  # Not stored in cache
                    merchant=tx_data.get('merchant'),
                    account_id=tx_data['account_id'],
                    category=tx_data.get('category'),
                    is_transfer=tx_data.get('is_transfer', False),
                    is_duplicate=tx_data.get('is_duplicate', False)
                )
                transactions.append(tx)

            # Analyze spending patterns
            spending_analysis = await self.analyze_spending_patterns(user_id, transactions)

            # Get debt accounts
            debt_result = self.supabase.table("debt_accounts").select("*").eq("user_id", user_id).execute()
            debt_accounts = debt_result.data if debt_result.data else []

            # Generate debt recommendations
            debt_recommendations = []
            if debt_accounts:
                debt_strategy = await self.suggest_debt_paydown_strategy(user_id, debt_accounts)
                debt_recommendations.append(debt_strategy)

            # Create budget templates
            budget_templates = []
            for category, analysis in spending_analysis.get('category_analysis', {}).items():
                template = {
                    'category_name': category,
                    'subcategory': 'auto_generated',
                    'merchant_patterns': [],  # Would be populated from merchant analysis
                    'typical_range_min': analysis['min_spending'],
                    'typical_range_max': analysis['max_spending'],
                    'is_essential': analysis['is_essential'],
                    'detection_confidence': analysis['confidence']
                }
                budget_templates.append(template)

            # Store budget templates
            if budget_templates:
                self.supabase.table("budget_templates").insert(budget_templates).execute()

            result = {
                'suggested_categories': [
                    {
                        'key': category,
                        'label': category.replace('_', ' ').title(),
                        'target': analysis['suggested_budget'],
                        'is_essential': analysis['is_essential'],
                        'confidence': analysis['confidence']
                    }
                    for category, analysis in spending_analysis.get('category_analysis', {}).items()
                ],
                'debt_recommendations': debt_recommendations,
                'budget_templates': budget_templates,
                'spending_insights': spending_analysis.get('insights', []),
                'total_analyzed': len(transactions)
            }

            logger.info(f"Budget generation complete: {len(result['suggested_categories'])} categories suggested")
            return result

        except Exception as e:
            logger.error(f"Error generating budget from patterns: {e}", exc_info=True)
            return {
                'error': str(e),
                'suggested_categories': [],
                'debt_recommendations': [],
                'budget_templates': []
            }


# Global AI instance
budget_ai = BudgetAI()
